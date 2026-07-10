"""
Speaking pace and pause detection from word-level audio timestamps.

Pure function over a list of {"word", "start", "end"} dicts (as returned
by voice_client.transcribe_with_word_timestamps) -- no I/O, fully
unit-testable with synthetic timing data.
"""

from app.modules.speech_analysis.schema import PauseEvent

LONG_PAUSE_THRESHOLD_SECONDS = 1.5

# A typical natural conversational speaking pace. Outside this range,
# communication_quality gets a mild penalty (see analyzer.py).
IDEAL_WPM_MIN = 110.0
IDEAL_WPM_MAX = 170.0


def analyze_pace_and_pauses(word_timestamps: list[dict]) -> tuple[float, float, list[PauseEvent]]:
    """Returns (speaking_duration_seconds, speaking_rate_wpm, long_pauses).

    speaking_duration_seconds spans from the first word's start to the
    last word's end -- i.e. the actual speech, excluding any leading or
    trailing silence in the recording.
    """
    if not word_timestamps:
        return 0.0, 0.0, []

    start_time = word_timestamps[0]["start"]
    end_time = word_timestamps[-1]["end"]
    duration = max(end_time - start_time, 0.001)  # guard against zero-division on single-word answers

    word_count = len(word_timestamps)
    wpm = round((word_count / duration) * 60, 1)

    long_pauses: list[PauseEvent] = []
    for prev_word, next_word in zip(word_timestamps, word_timestamps[1:]):
        gap = next_word["start"] - prev_word["end"]
        if gap >= LONG_PAUSE_THRESHOLD_SECONDS:
            long_pauses.append(
                PauseEvent(
                    start_seconds=round(prev_word["end"], 2),
                    end_seconds=round(next_word["start"], 2),
                    duration_seconds=round(gap, 2),
                )
            )

    return round(duration, 2), wpm, long_pauses
