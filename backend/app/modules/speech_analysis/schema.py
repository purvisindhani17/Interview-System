"""
Pydantic schema for speech analysis (Step 7 of the workflow).

Like cv_analysis, everything here is computed deterministically from the
transcript text and word-level audio timestamps -- no LLM involved. This
keeps pace/filler/clarity numbers reproducible; genuinely subjective
judgment about answer quality is Module 8's job.
"""

from pydantic import BaseModel, Field


class FillerWordBreakdown(BaseModel):
    word: str
    count: int


class PauseEvent(BaseModel):
    start_seconds: float
    end_seconds: float
    duration_seconds: float


class SpeechAnalysisResult(BaseModel):
    turn_number: int
    word_count: int = 0
    speaking_duration_seconds: float = 0.0
    speaking_rate_wpm: float = 0.0

    filler_word_count: int = 0
    filler_word_rate_per_100_words: float = 0.0
    filler_word_breakdown: list[FillerWordBreakdown] = Field(default_factory=list)

    long_pauses: list[PauseEvent] = Field(default_factory=list)
    long_pause_count: int = 0
    total_pause_duration_seconds: float = 0.0

    average_sentence_length_words: float = 0.0
    clarity_score: float = 0.0  # 0-100
    confidence_score: float = 0.0  # 0-100
    communication_quality_score: float = 0.0  # 0-100, blended

    notes: list[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "turn_number": 2,
                "word_count": 84,
                "speaking_duration_seconds": 31.4,
                "speaking_rate_wpm": 160.5,
                "filler_word_count": 3,
                "filler_word_rate_per_100_words": 3.6,
                "filler_word_breakdown": [{"word": "um", "count": 2}, {"word": "like", "count": 1}],
                "long_pauses": [],
                "long_pause_count": 0,
                "total_pause_duration_seconds": 0.0,
                "average_sentence_length_words": 18.2,
                "clarity_score": 88.0,
                "confidence_score": 82.0,
                "communication_quality_score": 85.4,
                "notes": ["Speaking pace is within a natural conversational range."],
            }
        }


class SpeechSessionSummary(BaseModel):
    session_id: str
    turns_analyzed: int = 0
    average_speaking_rate_wpm: float = 0.0
    average_filler_word_rate_per_100_words: float = 0.0
    total_long_pauses: int = 0
    average_clarity_score: float = 0.0
    average_confidence_score: float = 0.0
    average_communication_quality_score: float = 0.0
