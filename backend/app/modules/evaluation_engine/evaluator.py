"""
LLM answer evaluation orchestration (Step 8 of the workflow).

Given a question and the candidate's transcribed answer (plus resume/JD
for grounding), asks the LLM to score each applicable dimension with a
reasoning explanation -- per your spec, "The LLM should also explain WHY
it assigned each evaluation." The deterministic overall_score is computed
afterward in aggregator.py, not by the LLM.
"""

from app.modules.evaluation_engine.aggregator import compute_overall_score
from app.modules.evaluation_engine.schema import AnswerEvaluation
from app.modules.job_parser.schema import ParsedJobDescription
from app.modules.resume_parser.schema import ParsedResume
from app.utils.llm_client import get_llm_json

SYSTEM_PROMPT = """You are an expert technical interviewer evaluating a candidate's answer
after the fact. You will be given the question asked, the candidate's transcribed spoken
answer, their resume, and the job description for grounding.

Return ONLY a single valid JSON object -- no markdown fences, no commentary -- with this shape:
{
  "is_behavioral_question": boolean,
  "technical_accuracy": {"score": number, "reasoning": string} or null,
  "depth_of_knowledge": {"score": number, "reasoning": string} or null,
  "problem_solving": {"score": number, "reasoning": string} or null,
  "behavioral_skills": {"score": number, "reasoning": string} or null,
  "star_method_adherence": {"score": number, "reasoning": string} or null,
  "communication": {"score": number, "reasoning": string},
  "confidence": {"score": number, "reasoning": string},
  "explanation_quality": {"score": number, "reasoning": string},
  "overall_summary": string
}

Rules:
- "is_behavioral_question": true if the question is primarily about past experience,
  teamwork, conflict, leadership, etc. rather than technical content.
- Technical dimensions ("technical_accuracy", "depth_of_knowledge", "problem_solving"):
  set to null if the question is purely behavioral with no technical content to assess.
  Otherwise, score based on correctness and depth relative to what the job description
  and resume suggest the candidate should know.
- Behavioral dimensions ("behavioral_skills", "star_method_adherence"): set to null if the
  question is purely technical with no behavioral content. Otherwise, "star_method_adherence"
  specifically assesses whether the answer follows Situation-Task-Action-Result structure.
- "communication": assesses the LOGICAL STRUCTURE and CLARITY of the answer's content and
  explanation flow -- NOT speaking pace, filler words, or pauses (those are measured
  separately by a different system). Judge whether the answer was organized and easy to follow.
- "confidence": assesses how confidently and directly the candidate asserted their claims in
  the answer's CONTENT (e.g. stating facts directly vs. hedging on things they should know) --
  not vocal tone or delivery.
- "explanation_quality": how well the candidate explained their reasoning/thought process,
  not just what they concluded.
- Every score is 0-100. Every dimension you DO score must include a specific "reasoning"
  string explaining WHY that score was given, grounded in what the candidate actually said.
- "overall_summary": 2-3 sentences summarizing the answer's overall quality for a hiring manager.
- Never invent claims the candidate didn't make. If the answer is very short or off-topic,
  score accordingly and say so in the reasoning rather than being generous.
"""


def evaluate_answer(
    question: str,
    answer_transcript: str,
    resume: ParsedResume,
    jd: ParsedJobDescription,
    turn_number: int,
) -> AnswerEvaluation:
    user_prompt = (
        f"QUESTION: {question}\n\n"
        f"CANDIDATE ANSWER (transcribed): {answer_transcript}\n\n"
        f"RESUME (for grounding):\n{resume.model_dump_json(indent=2)}\n\n"
        f"JOB DESCRIPTION (for grounding):\n{jd.model_dump_json(indent=2)}\n"
    )

    llm_result = get_llm_json(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)

    evaluation = AnswerEvaluation(
        turn_number=turn_number,
        question=question,
        **llm_result,
    )
    evaluation.overall_score = compute_overall_score(evaluation)
    return evaluation
