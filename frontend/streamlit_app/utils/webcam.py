"""
streamlit-webrtc video frame processor for continuous webcam capture.

streamlit-webrtc runs frame processing in a background thread that is
NOT the Streamlit script-execution context, so it cannot safely read or
write st.session_state directly. Instead, everything the processor needs
(session_id, backend URL) is passed in at construction time as plain
attributes, and captured frames are POSTed to the backend from a
short-lived background thread (fire-and-forget) so the video pipeline
itself is never blocked waiting on a network call -- this keeps the live
video feed smooth while still sampling frames for Module 6's attention
tracking roughly every CAPTURE_INTERVAL_SECONDS.
"""

import threading
import time

import av
import cv2
import requests

CAPTURE_INTERVAL_SECONDS = 3.0


class AttentionTrackingProcessor:
    def __init__(self, session_id: str, backend_url: str):
        self.session_id = session_id
        self.backend_url = backend_url.rstrip("/")
        self._last_capture_time = 0.0
        self._lock = threading.Lock()

    def _post_frame_async(self, jpeg_bytes: bytes) -> None:
        def _send():
            try:
                requests.post(
                    f"{self.backend_url}/cv/session/{self.session_id}/frame",
                    files={"frame": ("frame.jpg", jpeg_bytes, "image/jpeg")},
                    timeout=15,
                )
            except requests.RequestException:
                pass  # best-effort; a missed frame just means one less CV sample

        threading.Thread(target=_send, daemon=True).start()

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        now = time.time()
        with self._lock:
            should_capture = (now - self._last_capture_time) >= CAPTURE_INTERVAL_SECONDS
            if should_capture:
                self._last_capture_time = now

        if should_capture:
            image = frame.to_ndarray(format="bgr24")
            ok, buf = cv2.imencode(".jpg", image)
            if ok:
                self._post_frame_async(buf.tobytes())

        return frame
