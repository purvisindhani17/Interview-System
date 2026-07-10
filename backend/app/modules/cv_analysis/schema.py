"""
Pydantic schema for computer vision analysis (Step 6 of the workflow).

Everything here is computed deterministically from OpenCV/MediaPipe
landmark geometry -- no LLM involved, matching the same "keep numbers
reproducible" principle as match_engine's scoring.
"""

from pydantic import BaseModel, Field


class FrameMetrics(BaseModel):
    frame_number: int
    face_visible: bool = False
    yaw_degrees: float | None = None
    pitch_degrees: float | None = None
    roll_degrees: float | None = None
    eye_contact: bool = False
    looking_away: bool = False
    looking_down: bool = False
    smiling: bool = False
    attention_score: float = 0.0  # 0-100, this single frame only


class CVSessionSummary(BaseModel):
    session_id: str
    total_frames_analyzed: int = 0
    face_visibility_percentage: float = 0.0
    eye_contact_percentage: float = 0.0
    looking_away_percentage: float = 0.0
    looking_down_percentage: float = 0.0
    smile_frequency_percentage: float = 0.0
    average_attention_score: float = 0.0
    dominant_face_orientation: str = "Unknown"

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123",
                "total_frames_analyzed": 42,
                "face_visibility_percentage": 97.6,
                "eye_contact_percentage": 81.0,
                "looking_away_percentage": 9.5,
                "looking_down_percentage": 4.8,
                "smile_frequency_percentage": 21.4,
                "average_attention_score": 78.3,
                "dominant_face_orientation": "Mostly centered, good eye contact",
            }
        }


class FrameAnalysisResponse(BaseModel):
    frame: FrameMetrics
    running_average_attention_score: float = Field(
        description="Average attention score across all frames analyzed so far this session."
    )
