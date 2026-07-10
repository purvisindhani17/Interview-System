"""
Confidence indicators: pure text pattern matching, no LLM.

Detects hedging language ("I think", "maybe", "I'm not sure") which are
well-established linguistic markers of reduced speaker confidence. This
is intentionally narrow and pattern-based -- judging whether the
*content* of an answer was confident/correct is Module 8's job; this
module only looks at *how* something was said.
"""

import re

HEDGING_PHRASES = [
    "i think", "i guess", "i suppose", "i'm not sure", "im not sure",
    "not sure", "maybe", "probably", "possibly", "might be",
    "kind of", "sort of", "i could be wrong", "correct me if i'm wrong",
]

_HEDGING_PATTERNS = [re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE) for phrase in HEDGING_PHRASES]


def count_hedging_phrases(transcript: str) -> int:
    return sum(len(pattern.findall(transcript)) for pattern in _HEDGING_PATTERNS)


def compute_confidence_score(
    transcript: str, word_count: int, filler_rate_per_100_words: float, long_pause_count: int
) -> float:
    """Heuristic 0-100 confidence score blending hedging language, filler
    rate, and pause frequency -- all speech-pattern signals, not content judgment."""
    if word_count == 0:
        return 0.0

    hedging_count = count_hedging_phrases(transcript)
    hedging_rate_per_100_words = (hedging_count / word_count) * 100

    score = 100.0
    score -= min(hedging_rate_per_100_words * 6.0, 40.0)  # hedging language is the strongest signal
    score -= min(filler_rate_per_100_words * 2.0, 25.0)
    score -= min(long_pause_count * 5.0, 20.0)

    return round(max(0.0, min(100.0, score)), 1)
