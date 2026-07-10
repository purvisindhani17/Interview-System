"""
Deterministic geometry computations from face landmarks.

Kept separate from face_analyzer.py (which handles MediaPipe/OpenCV I/O)
so these pure math functions can be unit-tested with synthetic landmark
coordinates, independent of whether a real face was actually detected in
an image.

Head pose uses the standard 6-point solvePnP technique with a generic
3D face model -- a well-established approach (not any single source's
proprietary code), using MediaPipe FaceMesh landmark indices:
  1   = nose tip
  152 = chin
  33  = left eye, left corner
  263 = right eye, right corner
  61  = left mouth corner
  291 = right mouth corner
"""

import cv2
import numpy as np

# Generic 3D face model points (arbitrary units, right-handed, nose tip at origin).
# These are the standard reference coordinates widely used for 6-point
# head-pose estimation; they approximate average adult facial geometry
# and don't need to be a perfect match for any individual face for the
# resulting yaw/pitch/roll angles to be directionally accurate.
_MODEL_POINTS_3D = np.array(
    [
        (0.0, 0.0, 0.0),  # nose tip
        (0.0, -330.0, -65.0),  # chin
        (-225.0, 170.0, -135.0),  # left eye left corner
        (225.0, 170.0, -135.0),  # right eye right corner
        (-150.0, -150.0, -125.0),  # left mouth corner
        (150.0, -150.0, -125.0),  # right mouth corner
    ],
    dtype=np.float64,
)

LANDMARK_INDICES = {
    "nose_tip": 1,
    "chin": 152,
    "left_eye_left_corner": 33,
    "right_eye_right_corner": 263,
    "left_mouth_corner": 61,
    "right_mouth_corner": 291,
}

# Thresholds (degrees) -- heuristic, not clinically validated. Tuned for a
# roughly frontal webcam angle typical of a laptop interview setup.
EYE_CONTACT_MAX_YAW = 15.0
EYE_CONTACT_MAX_PITCH = 15.0
LOOKING_AWAY_MIN_YAW = 25.0
LOOKING_DOWN_MIN_PITCH = 20.0

# Heuristic smile threshold: mouth width relative to inter-ocular distance.
# Calibrated against a neutral-expression reference face; a genuine smile
# stretches the mouth corners noticeably wider relative to eye spacing.
SMILE_WIDTH_RATIO_THRESHOLD = 0.62


def estimate_head_pose(
    landmark_points_2d: dict[str, tuple[float, float]], image_width: int, image_height: int
) -> tuple[float, float, float]:
    """Estimate (pitch, yaw, roll) in degrees from 6 named 2D landmark points.

    Uses solvePnP with an approximated camera matrix (focal length ~= image
    width, principal point at image center, no lens distortion) -- the
    standard simplification when no camera calibration is available.
    """
    image_points_2d = np.array(
        [
            landmark_points_2d["nose_tip"],
            landmark_points_2d["chin"],
            landmark_points_2d["left_eye_left_corner"],
            landmark_points_2d["right_eye_right_corner"],
            landmark_points_2d["left_mouth_corner"],
            landmark_points_2d["right_mouth_corner"],
        ],
        dtype=np.float64,
    )

    focal_length = image_width
    center = (image_width / 2, image_height / 2)
    camera_matrix = np.array(
        [[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]], dtype=np.float64
    )
    dist_coeffs = np.zeros((4, 1))  # assume no lens distortion

    # A minimal 6-point PnP solve has a well-known pose ambiguity (two
    # near-equally-valid solutions related by a ~180-degree flip). Seeding
    # with an extrinsic guess of "facing the camera, a plausible distance
    # away" biases solvePnP toward the physically correct solution instead
    # of its mirror-image alternative.
    rvec_init = np.zeros((3, 1), dtype=np.float64)
    tvec_init = np.array([[0.0], [0.0], [1000.0]], dtype=np.float64)

    success, rotation_vector, _ = cv2.solvePnP(
        _MODEL_POINTS_3D,
        image_points_2d,
        camera_matrix,
        dist_coeffs,
        rvec_init,
        tvec_init,
        useExtrinsicGuess=True,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )
    if not success:
        raise ValueError("solvePnP failed to converge on a head pose solution.")

    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)

    # Decompose rotation matrix into Euler angles (pitch, yaw, roll) in degrees.
    sy = np.sqrt(rotation_matrix[0, 0] ** 2 + rotation_matrix[1, 0] ** 2)
    singular = sy < 1e-6

    if not singular:
        pitch = np.arctan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
        yaw = np.arctan2(-rotation_matrix[2, 0], sy)
        roll = np.arctan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
    else:
        pitch = np.arctan2(-rotation_matrix[1, 2], rotation_matrix[1, 1])
        yaw = np.arctan2(-rotation_matrix[2, 0], sy)
        roll = 0.0

    pitch_deg = float(np.degrees(pitch))
    yaw_deg = float(np.degrees(yaw))
    roll_deg = float(np.degrees(roll))

    # Even with the extrinsic guess above, the residual ambiguity can still
    # occasionally surface as a pitch near +/-180 (its mirror-flip form)
    # while yaw/roll land correctly. Fold it back into the physically
    # plausible +/-90 degree range.
    if pitch_deg > 90:
        pitch_deg -= 180
    elif pitch_deg < -90:
        pitch_deg += 180

    return pitch_deg, yaw_deg, roll_deg


def detect_smile(landmark_points_2d: dict[str, tuple[float, float]]) -> bool:
    """Heuristic smile detection: mouth width relative to inter-ocular distance."""
    left_eye = np.array(landmark_points_2d["left_eye_left_corner"])
    right_eye = np.array(landmark_points_2d["right_eye_right_corner"])
    left_mouth = np.array(landmark_points_2d["left_mouth_corner"])
    right_mouth = np.array(landmark_points_2d["right_mouth_corner"])

    inter_ocular_distance = float(np.linalg.norm(right_eye - left_eye))
    mouth_width = float(np.linalg.norm(right_mouth - left_mouth))

    if inter_ocular_distance == 0:
        return False

    return (mouth_width / inter_ocular_distance) >= SMILE_WIDTH_RATIO_THRESHOLD


def classify_gaze(pitch_deg: float, yaw_deg: float) -> tuple[bool, bool, bool]:
    """Return (eye_contact, looking_away, looking_down) booleans from head pose angles."""
    looking_down = pitch_deg >= LOOKING_DOWN_MIN_PITCH
    looking_away = abs(yaw_deg) >= LOOKING_AWAY_MIN_YAW or (
        pitch_deg <= -LOOKING_DOWN_MIN_PITCH  # looking sharply up counts as "away" too
    )
    eye_contact = (
        abs(yaw_deg) <= EYE_CONTACT_MAX_YAW
        and abs(pitch_deg) <= EYE_CONTACT_MAX_PITCH
        and not looking_away
        and not looking_down
    )
    return eye_contact, looking_away, looking_down


def compute_attention_score(
    face_visible: bool, eye_contact: bool, looking_away: bool, looking_down: bool
) -> float:
    """Heuristic 0-100 attention score for a single frame."""
    if not face_visible:
        return 0.0

    score = 100.0
    if looking_away:
        score -= 40.0
    if looking_down:
        score -= 25.0
    if not eye_contact and not looking_away and not looking_down:
        # Face visible and not flagged as away/down, but gaze is still off-center
        # enough to miss the strict eye-contact threshold -- mild penalty.
        score -= 15.0

    return max(0.0, min(100.0, score))
