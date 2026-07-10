"""
MediaPipe FaceLandmarker wrapper (Step 6: Computer Vision Analysis).

Uses MediaPipe's current Tasks API (mediapipe.tasks.python.vision.FaceLandmarker)
rather than the legacy mp.solutions.face_mesh API, which was removed in
MediaPipe releases from 0.10.18 onward. The Tasks API needs a small model
bundle downloaded once (handled transparently by model_setup.py) instead of
shipping the model inside the pip package.

This is the only file in cv_analysis that touches MediaPipe/OpenCV I/O
directly -- geometry.py holds the pure math so it can be unit-tested
without needing an actual face detection to succeed.
"""

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

from app.modules.cv_analysis.geometry import (
    LANDMARK_INDICES,
    classify_gaze,
    compute_attention_score,
    detect_smile,
    estimate_head_pose,
)
from app.modules.cv_analysis.model_setup import ensure_face_landmarker_model
from app.modules.cv_analysis.schema import FrameMetrics

# The landmarker is expensive to initialize, so we keep one lazily-created
# module-level instance rather than building a new one per request.
# running_mode=IMAGE is appropriate here since each API call analyzes one
# independent snapshot (captured periodically by the frontend), not a
# continuous video stream within a single process.
_landmarker: vision.FaceLandmarker | None = None


def _get_landmarker() -> vision.FaceLandmarker:
    global _landmarker
    if _landmarker is None:
        model_path = ensure_face_landmarker_model()
        options = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        _landmarker = vision.FaceLandmarker.create_from_options(options)
    return _landmarker


def analyze_frame(image_bgr: np.ndarray, frame_number: int) -> FrameMetrics:
    """Run MediaPipe FaceLandmarker on a single BGR image and compute all Step-6 metrics."""
    height, width = image_bgr.shape[:2]
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)

    result = _get_landmarker().detect(mp_image)

    if not result.face_landmarks:
        return FrameMetrics(frame_number=frame_number, face_visible=False, attention_score=0.0)

    landmarks = result.face_landmarks[0]

    landmark_points_2d = {
        name: (landmarks[idx].x * width, landmarks[idx].y * height)
        for name, idx in LANDMARK_INDICES.items()
    }

    try:
        pitch, yaw, roll = estimate_head_pose(landmark_points_2d, width, height)
    except ValueError:
        # solvePnP failed to converge (rare, degenerate geometry) -- report
        # the face as visible but without reliable pose-derived metrics.
        return FrameMetrics(frame_number=frame_number, face_visible=True, attention_score=50.0)

    eye_contact, looking_away, looking_down = classify_gaze(pitch, yaw)
    smiling = detect_smile(landmark_points_2d)
    attention_score = compute_attention_score(True, eye_contact, looking_away, looking_down)

    return FrameMetrics(
        frame_number=frame_number,
        face_visible=True,
        yaw_degrees=round(yaw, 1),
        pitch_degrees=round(pitch, 1),
        roll_degrees=round(roll, 1),
        eye_contact=eye_contact,
        looking_away=looking_away,
        looking_down=looking_down,
        smiling=smiling,
        attention_score=attention_score,
    )


def decode_image(image_bytes: bytes) -> np.ndarray:
    """Decode uploaded image bytes (jpg/png) into an OpenCV BGR array."""
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image -- unsupported format or corrupted data.")
    return image
