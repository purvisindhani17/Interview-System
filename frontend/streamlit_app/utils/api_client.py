

import requests
import streamlit as st

DEFAULT_TIMEOUT = 60
LONG_TIMEOUT = 120  # LLM/voice calls can be slower than a typical API request


class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{status_code}] {detail}")


def _base_url() -> str:
    return st.session_state.get("backend_url", "http://127.0.0.1:8000").rstrip("/")


def _request(method: str, url: str, **kwargs) -> requests.Response:
    try:
        return requests.request(method, url, **kwargs)
    except requests.RequestException as e:
        raise APIError(503, f"Could not reach the backend at {url}: {e}") from e


def _handle(response: requests.Response) -> dict:
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise APIError(response.status_code, detail)
    return response.json()


def health_check() -> bool:
    try:
        r = requests.get(f"{_base_url()}/health", timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


# --- Module 1: Resume ---
def upload_resume(file_bytes: bytes, filename: str) -> dict:
    files = {"file": (filename, file_bytes, "application/pdf")}
    r = _request("POST", f"{_base_url()}/resume/upload", files=files, timeout=LONG_TIMEOUT)
    return _handle(r)


# --- Module 2: Job Description ---
def parse_job_description(
    text: str | None = None, file_bytes: bytes | None = None, filename: str = "jd.txt"
) -> dict:
    data = {"text": text} if text else {}
    files = {"file": (filename, file_bytes)} if file_bytes else None
    r = _request(
        "POST", f"{_base_url()}/job-description/parse", data=data, files=files, timeout=LONG_TIMEOUT
    )
    return _handle(r)


# --- Module 3: Match ---
def compare_resume_and_jd(resume_id: str, jd_id: str) -> dict:
    r = _request(
        "POST",
        f"{_base_url()}/match/compare",
        json={"resume_id": resume_id, "jd_id": jd_id},
        timeout=LONG_TIMEOUT,
    )
    return _handle(r)


# --- Module 4: Interview Plan ---
def generate_plan(resume_id: str, jd_id: str, match_id: str) -> dict:
    r = _request(
        "POST",
        f"{_base_url()}/interview/plan",
        json={"resume_id": resume_id, "jd_id": jd_id, "match_id": match_id},
        timeout=LONG_TIMEOUT,
    )
    return _handle(r)


# --- Module 5: Live Interview ---
def start_session(plan_id: str) -> dict:
    r = _request(
        "POST", f"{_base_url()}/interview/session/start", json={"plan_id": plan_id}, timeout=LONG_TIMEOUT
    )
    return _handle(r)


def submit_answer(session_id: str, audio_bytes: bytes, filename: str = "answer.wav") -> dict:
    files = {"audio": (filename, audio_bytes, "audio/wav")}
    data = {"session_id": session_id}
    r = _request(
        "POST", f"{_base_url()}/interview/session/answer", data=data, files=files, timeout=LONG_TIMEOUT
    )
    return _handle(r)


def audio_url(path: str) -> str:
    """Convert a backend-relative /audio/... path into a full URL for st.audio()."""
    if path.startswith("http"):
        return path
    return f"{_base_url()}{path}"


# --- Module 6: Computer Vision ---
def submit_cv_frame(session_id: str, image_bytes: bytes) -> dict:
    files = {"frame": ("frame.jpg", image_bytes, "image/jpeg")}
    r = _request(
        "POST", f"{_base_url()}/cv/session/{session_id}/frame", files=files, timeout=DEFAULT_TIMEOUT
    )
    return _handle(r)


def get_cv_summary(session_id: str) -> dict | None:
    r = _request("GET", f"{_base_url()}/cv/session/{session_id}/summary", timeout=DEFAULT_TIMEOUT)
    if r.status_code == 404:
        return None
    return _handle(r)


# --- Module 7: Speech Analysis ---
def analyze_speech(session_id: str, turn_number: int) -> dict:
    r = _request(
        "POST",
        f"{_base_url()}/speech/session/{session_id}/analyze/{turn_number}",
        timeout=LONG_TIMEOUT,
    )
    return _handle(r)


def get_speech_summary(session_id: str) -> dict | None:
    r = _request("GET", f"{_base_url()}/speech/session/{session_id}/summary", timeout=DEFAULT_TIMEOUT)
    if r.status_code == 404:
        return None
    return _handle(r)


# --- Module 8: Answer Evaluation ---
def evaluate_answer(session_id: str, turn_number: int) -> dict:
    r = _request(
        "POST",
        f"{_base_url()}/evaluation/session/{session_id}/evaluate/{turn_number}",
        timeout=LONG_TIMEOUT,
    )
    return _handle(r)


def get_evaluation_summary(session_id: str) -> dict | None:
    r = _request(
        "GET", f"{_base_url()}/evaluation/session/{session_id}/summary", timeout=DEFAULT_TIMEOUT
    )
    if r.status_code == 404:
        return None
    return _handle(r)


# --- Module 9: Scoring ---
def get_overall_score(session_id: str) -> dict:
    r = _request("GET", f"{_base_url()}/score/session/{session_id}", timeout=DEFAULT_TIMEOUT)
    return _handle(r)


# --- Module 10: Report ---
def get_report(session_id: str) -> dict:
    r = _request("GET", f"{_base_url()}/report/session/{session_id}", timeout=LONG_TIMEOUT)
    return _handle(r)
