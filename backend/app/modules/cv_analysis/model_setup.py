"""
One-time download of the MediaPipe Face Landmarker model bundle.

Newer MediaPipe releases (0.10.18+) removed the legacy `mp.solutions.face_mesh`
API that used to ship its model inside the pip package itself. The current
Tasks API (`mediapipe.tasks.python.vision.FaceLandmarker`) instead needs a
~4MB `.task` model bundle downloaded once from Google's model repository.
This module handles that download transparently on first use and caches
the file locally so it only ever happens once per machine.
"""

import os
import urllib.request

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/latest/face_landmarker.task"
)
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "face_landmarker.task")


class ModelDownloadError(Exception):
    pass


def ensure_face_landmarker_model() -> str:
    """Return a local path to the Face Landmarker model, downloading it on
    first use if it isn't already cached. Raises ModelDownloadError with a
    manual-download fallback message if the automatic download fails (e.g.
    storage.googleapis.com is blocked on some networks)."""
    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 0:
        return MODEL_PATH

    os.makedirs(MODEL_DIR, exist_ok=True)
    tmp_path = MODEL_PATH + ".part"

    try:
        urllib.request.urlretrieve(MODEL_URL, tmp_path)
        os.replace(tmp_path, MODEL_PATH)
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise ModelDownloadError(
            f"Could not download the Face Landmarker model automatically ({e}). "
            f"Download it manually from:\n  {MODEL_URL}\n"
            f"and save it to:\n  {MODEL_PATH}"
        ) from e

    return MODEL_PATH
