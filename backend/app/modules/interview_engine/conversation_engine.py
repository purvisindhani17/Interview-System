"""
Live interview conversation engine (Module 5, Steps 5 + 9).

Two LLM-backed responsibilities, each isolated so they can be reasoned
about (and tested) independently:

1. quick_evaluate_answer -- a fast, single-dimension correctness signal
   ("correct" / "partial" / "incorrect") used ONLY to drive adaptive
   routing (difficulty_engine.py) during the live conversation. This is
   intentionally shallow; Module 8 does the real multi-dimensional
   evaluation after the fact.

2. generate_next_question -- given the interview plan, full conversation
   history so far, and the current adaptive state (difficulty/topic),
   produces the next question. The LLM decides whether to go deeper on
   the previous topic, move to the next one, follow up on a project, or
   wrap up the interview -- never from a predefined list, per the spec.
"""

from app.modules.interview_engine.schema import (
    ConversationTurn,
    InterviewPlan,
    InterviewSession,
    QuickAssessment,
)
from app.modules.job_parser.schema import ParsedJobDescription
from app.modules.resume_parser.schema import ParsedResume
from app.utils.llm_client import get_llm_json

QUICK_EVAL_SYSTEM_PROMPT = """You are assisting a live technical interview. You will be given the
question that was just asked and the candidate's transcribed spoken answer.
Return ONLY a single valid JSON object -- no markdown fences, no commentary:
{
  "correctness": "correct" | "partial" | "incorrect",
  "note": string
}

Rules:
- "correct": the answer is technically sound and reasonably complete for the question asked.
- "partial": the answer is on the right track but incomplete, vague, or has minor gaps.
- "incorrect": the answer is wrong, off-topic, or the candidate clearly didn't know.
- "note": one short sentence justifying the label -- this is for internal routing logic,
  not shown to the candidate.
- This is a fast, single-dimension read for adaptive difficulty purposes only, not a full
  evaluation. Do not overthink it.
"""

NEXT_QUESTION_SYSTEM_PROMPT = """You are conducting a live, adaptive technical interview. You will be
given: the original interview plan/strategy, the candidate's resume and the job description for
grounding, the full conversation so far (questions asked, answers given, and quick correctness
assessments), and the current adaptive state (difficulty level and which plan topic we're on).

Return ONLY a single valid JSON object -- no markdown fences, no commentary:
{
  "question": string,
  "topic": string,
  "is_final_question": boolean,
  "reasoning": string
}

Rules:
- Never repeat a question already asked in the conversation history.
- The question must depend on: the interview plan, the job description, the candidate's resume,
  and specifically the previous answer and its quick assessment -- not a generic question bank.
- If the last answer was "correct", ask a harder follow-up on the same topic OR move to a new,
  more advanced topic from the plan.
- If the last answer was "incorrect" or weak, either ask an easier question on the same topic to
  find the candidate's actual level, or move to a different topic if this one seems exhausted.
- If the candidate has performed well across multiple questions on the current topic, move to
  the next topic_priorities entry from the plan rather than continuing to drill the same area.
- If the candidate mentioned a specific project in a previous answer that matches one of the
  plan's project_follow_ups, and it hasn't been asked about yet, prioritize that follow-up question.
- Set "is_final_question" to true if the conversation has reasonably covered the plan's topics and
  reached (or is close to) the plan's estimated_question_count, or if further questions wouldn't add
  new signal. Otherwise false.
- "topic" should be a short label (e.g. "Docker/Containerization", "Behavioral - STAR") describing
  what this new question is testing.
- "reasoning": one internal sentence on why this question was chosen next (not shown to candidate).
- The interview should never feel scripted -- ground every question in what's actually happened
  in the conversation so far.
"""


def quick_evaluate_answer(question: str, answer_transcript: str) -> QuickAssessment:
    user_prompt = f"QUESTION: {question}\n\nCANDIDATE ANSWER (transcribed): {answer_transcript}"
    result = get_llm_json(system_prompt=QUICK_EVAL_SYSTEM_PROMPT, user_prompt=user_prompt)
    return QuickAssessment(**result)


def _format_history(history: list[ConversationTurn]) -> str:
    if not history:
        return "(no questions asked yet)"

    lines = []
    for turn in history:
        lines.append(f"Q{turn.turn_number} [{turn.topic} / {turn.difficulty}]: {turn.question}")
        if turn.answer_transcript:
            lines.append(f"A{turn.turn_number}: {turn.answer_transcript}")
        if turn.quick_assessment:
            lines.append(
                f"  (quick assessment: {turn.quick_assessment.correctness} -- {turn.quick_assessment.note})"
            )
    return "\n".join(lines)


def generate_next_question(
    session: InterviewSession,
    plan: InterviewPlan,
    resume: ParsedResume,
    jd: ParsedJobDescription,
) -> dict:
    """Returns a dict with keys: question, topic, is_final_question, reasoning."""
    user_prompt = (
        f"INTERVIEW PLAN:\n{plan.model_dump_json(indent=2)}\n\n"
        f"RESUME:\n{resume.model_dump_json(indent=2)}\n\n"
        f"JOB DESCRIPTION:\n{jd.model_dump_json(indent=2)}\n\n"
        f"CONVERSATION SO FAR:\n{_format_history(session.history)}\n\n"
        f"CURRENT ADAPTIVE STATE: difficulty={session.current_difficulty}, "
        f"topic_index={session.current_topic_index} "
        f"(plan has {len(plan.topic_priorities)} prioritized topics), "
        f"questions_asked={len(session.history)}, "
        f"plan_estimated_question_count={plan.estimated_question_count}"
    )

    return get_llm_json(system_prompt=NEXT_QUESTION_SYSTEM_PROMPT, user_prompt=user_prompt)
