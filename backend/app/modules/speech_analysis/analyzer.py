"""
Speech analysis orchestration (Step 7 of the workflow).

Combines word-timestamped transcription (Whisper) with the deterministic
filler-word, pace/pause, clarity, and confidence analyzers into one
SpeechAnalysisResult per answer. Entirely LLM-free, consistent with
cv_analysis's design.
"""

from app.modules.speech_analysis.clarity_analyzer import analyze_clarity
from app.modules.speech_analysis.confidence_analyzer import compute_confidence_score
from app.modules.speech_analysis.filler_words import count_filler_words, count_words
from app.modules.speech_analysis.pace_analyzer import (
    IDEAL_WPM_MAX,
    IDEAL_WPM_MIN,
    analyze_pace_and_pauses,
)
from app.modules.speech_analysis.schema import SpeechAnalysisResult
from app.utils.voice_client import transcribe_with_word_timestamps

# Weights for blending clarity/confidence/pace into communication_quality_score.
CLARITY_WEIGHT = 0.4
CONFIDENCE_WEIGHT = 0.3
PACE_WEIGHT = 0.3


def _pace_score(wpm: float) -> float:
    """100 if within the ideal conversational range, tapering off outside it."""
    if wpm <= 0:
        return 0.0
    if IDEAL_WPM_MIN <= wpm <= IDEAL_WPM_MAX:
        return 100.0
    if wpm < IDEAL_WPM_MIN:
        deviation = IDEAL_WPM_MIN - wpm
    else:
        deviation = wpm - IDEAL_WPM_MAX
    return round(max(0.0, 100.0 - deviation * 1.5), 1)


def _build_notes(
    wpm: float, filler_rate: float, long_pause_count: int, total_pause_duration: float, clarity_score: float
) -> list[str]:
    notes = []

    if wpm > IDEAL_WPM_MAX:
        notes.append(f"Speaking pace is fast ({wpm} WPM) -- consider slowing down for clarity.")
    elif 0 < wpm < IDEAL_WPM_MIN:
        notes.append(f"Speaking pace is slow ({wpm} WPM), which may read as hesitant.")
    elif wpm > 0:
        notes.append("Speaking pace is within a natural conversational range.")

    if filler_rate >= 8.0:
        notes.append(f"High filler word usage ({filler_rate} per 100 words).")
    elif filler_rate >= 4.0:
        notes.append(f"Moderate filler word usage ({filler_rate} per 100 words).")

    if long_pause_count > 0:
        notes.append(
            f"{long_pause_count} long pause(s) detected, totaling {total_pause_duration}s -- "
            "may indicate uncertainty or time spent formulating the answer."
        )

    if clarity_score < 60:
        notes.append("Sentence structure suggests rambling or overly fragmented delivery.")

    return notes


def analyze_answer_speech(turn_number: int, transcript: str, audio_path: str) -> SpeechAnalysisResult:
    word_timestamps = transcribe_with_word_timestamps(audio_path)

    word_count = count_words(transcript)
    filler_count, filler_breakdown = count_filler_words(transcript)
    filler_rate = round((filler_count / word_count) * 100, 1) if word_count else 0.0

    duration, wpm, long_pauses = analyze_pace_and_pauses(word_timestamps)
    total_pause_duration = round(sum(p.duration_seconds for p in long_pauses), 1)

    avg_sentence_length, clarity_score = analyze_clarity(transcript)
    confidence_score = compute_confidence_score(transcript, word_count, filler_rate, len(long_pauses))
    pace_score = _pace_score(wpm)

    communication_quality = round(
        clarity_score * CLARITY_WEIGHT + confidence_score * CONFIDENCE_WEIGHT + pace_score * PACE_WEIGHT, 1
    )

    notes = _build_notes(wpm, filler_rate, len(long_pauses), total_pause_duration, clarity_score)

    return SpeechAnalysisResult(
        turn_number=turn_number,
        word_count=word_count,
        speaking_duration_seconds=duration,
        speaking_rate_wpm=wpm,
        filler_word_count=filler_count,
        filler_word_rate_per_100_words=filler_rate,
        filler_word_breakdown=filler_breakdown,
        long_pauses=long_pauses,
        long_pause_count=len(long_pauses),
        total_pause_duration_seconds=total_pause_duration,
        average_sentence_length_words=avg_sentence_length,
        clarity_score=clarity_score,
        confidence_score=confidence_score,
        communication_quality_score=communication_quality,
        notes=notes,
    )
