"""
Deterministic difficulty adjustment (Step 9: Adaptive Interview).

Same design principle as match_engine's scoring: the *decision* of how
correctness maps to a difficulty change is a simple, reproducible state
machine, not something left to the LLM to decide inconsistently turn to
turn. The LLM's job (in conversation_engine.py) is only to produce the
`correctness` judgment and the actual next question text -- both of which
genuinely need language understanding. Once we have that judgment, moving
up/down a fixed difficulty ladder is plain logic.
"""

from app.modules.interview_engine.schema import DIFFICULTY_LEVELS


def next_difficulty(current_difficulty: str, correctness: str) -> str:
    """Return the next difficulty level given the current one and how the
    candidate did on the last question.

    - "correct"   -> step up one level (caps at "hard")
    - "incorrect" -> step down one level (floors at "easy")
    - "partial"   -> stay the same
    """
    if current_difficulty not in DIFFICULTY_LEVELS:
        current_difficulty = "medium"

    index = DIFFICULTY_LEVELS.index(current_difficulty)

    if correctness == "correct":
        index = min(index + 1, len(DIFFICULTY_LEVELS) - 1)
    elif correctness == "incorrect":
        index = max(index - 1, 0)
    # "partial" (or any unrecognized value) leaves index unchanged.

    return DIFFICULTY_LEVELS[index]
