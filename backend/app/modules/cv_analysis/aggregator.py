"""
Aggregates per-frame CV metrics into a session-level summary.

Pure function over a list of FrameMetrics -- no I/O -- so it's trivially
unit-testable without needing real frames or a real MediaPipe call.
"""

from app.modules.cv_analysis.schema import CVSessionSummary, FrameMetrics


def summarize_session(session_id: str, frames: list[FrameMetrics]) -> CVSessionSummary:
    if not frames:
        return CVSessionSummary(session_id=session_id, total_frames_analyzed=0)

    total = len(frames)
    visible_frames = [f for f in frames if f.face_visible]
    n_visible = len(visible_frames)

    face_visibility_pct = round((n_visible / total) * 100, 1)
    eye_contact_pct = round((sum(1 for f in visible_frames if f.eye_contact) / n_visible) * 100, 1) if n_visible else 0.0
    looking_away_pct = round((sum(1 for f in visible_frames if f.looking_away) / n_visible) * 100, 1) if n_visible else 0.0
    looking_down_pct = round((sum(1 for f in visible_frames if f.looking_down) / n_visible) * 100, 1) if n_visible else 0.0
    smile_pct = round((sum(1 for f in visible_frames if f.smiling) / n_visible) * 100, 1) if n_visible else 0.0
    avg_attention = round(sum(f.attention_score for f in frames) / total, 1)

    dominant_face_orientation = _describe_orientation(
        face_visibility_pct, eye_contact_pct, looking_away_pct, looking_down_pct
    )

    return CVSessionSummary(
        session_id=session_id,
        total_frames_analyzed=total,
        face_visibility_percentage=face_visibility_pct,
        eye_contact_percentage=eye_contact_pct,
        looking_away_percentage=looking_away_pct,
        looking_down_percentage=looking_down_pct,
        smile_frequency_percentage=smile_pct,
        average_attention_score=avg_attention,
        dominant_face_orientation=dominant_face_orientation,
    )


def _describe_orientation(
    face_visibility_pct: float, eye_contact_pct: float, looking_away_pct: float, looking_down_pct: float
) -> str:
    """A short, deterministic plain-English label summarizing overall camera behavior."""
    if face_visibility_pct < 50:
        return "Face frequently not visible to camera"
    if looking_away_pct >= 30:
        return "Frequently looking away from camera"
    if looking_down_pct >= 30:
        return "Frequently looking down"
    if eye_contact_pct >= 70:
        return "Mostly centered, good eye contact"
    if eye_contact_pct >= 40:
        return "Moderate eye contact, some drifting"
    return "Limited eye contact with camera"
