"""
Filler word detection: pure regex/text matching, no LLM.

Handles both single-word fillers ("um", "uh", "like") and multi-word
hedging phrases ("you know", "sort of") via word-boundary-aware regex,
case-insensitive.
"""

import re
from collections import Counter

from app.modules.speech_analysis.schema import FillerWordBreakdown

FILLER_WORDS = [
    "um", "umm", "uh", "uhh", "er", "erm",
    "like", "basically", "actually", "literally", "essentially",
    "you know", "i mean", "sort of", "kind of",
    "so yeah", "right,",
]

_FILLER_PATTERNS = {
    phrase: re.compile(r"\b" + re.escape(phrase.rstrip(",")) + r"\b", re.IGNORECASE)
    for phrase in FILLER_WORDS
}


def count_filler_words(transcript: str) -> tuple[int, list[FillerWordBreakdown]]:
    """Return (total_filler_count, breakdown_by_word) for a transcript."""
    counts: Counter[str] = Counter()

    for phrase, pattern in _FILLER_PATTERNS.items():
        matches = pattern.findall(transcript)
        if matches:
            counts[phrase.rstrip(",")] += len(matches)

    total = sum(counts.values())
    breakdown = [
        FillerWordBreakdown(word=word, count=count)
        for word, count in sorted(counts.items(), key=lambda kv: -kv[1])
    ]
    return total, breakdown


def count_words(transcript: str) -> int:
    """Simple whitespace word count, used as the denominator for filler rate and WPM."""
    return len([w for w in transcript.split() if w.strip()])
