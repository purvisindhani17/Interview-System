"""
Aggregates per-turn speech metrics into a session-level summary.
Pure function, no I/O -- trivially unit-testable.
"""

from app.modules.speech_analysis.schema import SpeechAnalysisResult, SpeechSessionSummary


def summarize_session(session_id: str, results: list[SpeechAnalysisResult]) -> SpeechSessionSummary:
    if not results:
        return SpeechSessionSummary(session_id=session_id, turns_analyzed=0)

    n = len(results)
    return SpeechSessionSummary(
        session_id=session_id,
        turns_analyzed=n,
        average_speaking_rate_wpm=round(sum(r.speaking_rate_wpm for r in results) / n, 1),
        average_filler_word_rate_per_100_words=round(
            sum(r.filler_word_rate_per_100_words for r in results) / n, 1
        ),
        total_long_pauses=sum(r.long_pause_count for r in results),
        average_clarity_score=round(sum(r.clarity_score for r in results) / n, 1),
        average_confidence_score=round(sum(r.confidence_score for r in results) / n, 1),
        average_communication_quality_score=round(
            sum(r.communication_quality_score for r in results) / n, 1
        ),
    )
