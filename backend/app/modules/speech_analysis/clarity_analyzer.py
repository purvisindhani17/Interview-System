"""
Sentence clarity heuristics: pure text analysis, no LLM.

Flags rambling (very long sentences) and fragmented, choppy delivery
(many very short sentences) -- both are common, easy-to-spot readability
signals a human interviewer would also notice.
"""

import re

LONG_SENTENCE_WORD_THRESHOLD = 35
SHORT_SENTENCE_WORD_THRESHOLD = 4


def split_sentences(transcript: str) -> list[str]:
    """Split transcript into sentences on ./?/! boundaries, dropping empties."""
    raw_sentences = re.split(r"[.!?]+", transcript)
    return [s.strip() for s in raw_sentences if s.strip()]


def analyze_clarity(transcript: str) -> tuple[float, float]:
    """Returns (average_sentence_length_words, clarity_score 0-100)."""
    sentences = split_sentences(transcript)

    if not sentences:
        return 0.0, 0.0

    sentence_lengths = [len(s.split()) for s in sentences]
    avg_length = round(sum(sentence_lengths) / len(sentence_lengths), 1)

    long_sentence_count = sum(1 for length in sentence_lengths if length > LONG_SENTENCE_WORD_THRESHOLD)
    short_sentence_count = sum(1 for length in sentence_lengths if length < SHORT_SENTENCE_WORD_THRESHOLD)

    long_ratio = long_sentence_count / len(sentences)
    short_ratio = short_sentence_count / len(sentences)

    score = 100.0
    score -= long_ratio * 35.0  # rambling, run-on sentences hurt clarity
    score -= short_ratio * 20.0  # overly fragmented delivery hurts clarity less severely

    return avg_length, round(max(0.0, min(100.0, score)), 1)
