"""
Report generation orchestration (Step 10 of the workflow).

Two clearly separated responsibilities, consistent with this project's
"LLM judges, code aggregates" principle:

1. Numeric scores are extracted deterministically from Module 9's
   OverallScoreResult plus two additional metrics (eye contact, confidence)
   that Module 9 doesn't weight into the overall score but the spec still
   wants reported.
2. The narrative sections (strengths, weaknesses, learning path, topics
   to practice, summary) are LLM-synthesized from all the underlying data
   -- this is exactly the kind of holistic judgment call an LLM is good
   at and hard-coded rules aren't.
"""

from app.modules.cv_analysis.schema import CVSessionSummary
from app.modules.evaluation_engine.schema import AnswerEvaluation, EvaluationSessionSummary
from app.modules.job_parser.schema import ParsedJobDescription
from app.modules.match_engine.schema import MatchResult
from app.modules.report_generator.schema import InterviewReport
from app.modules.resume_parser.schema import ParsedResume
from app.modules.scoring_engine.schema import OverallScoreResult
from app.modules.speech_analysis.schema import SpeechSessionSummary
from app.utils.llm_client import get_llm_json

SYSTEM_PROMPT = """You are writing the final summary section of a technical interview report for a
hiring manager. You will be given: the candidate's resume, the job description, the resume-vs-JD
match analysis, a breakdown of per-answer evaluations (each with dimension scores and the
interviewer's stated reasoning), computer-vision attention metrics, and speech delivery metrics.

Return ONLY a single valid JSON object -- no markdown fences, no commentary -- with this shape:
{
  "strengths": [string],
  "weaknesses": [string],
  "recommended_learning_path": [string],
  "topics_to_practice": [string],
  "interview_summary": string
}

Rules:
- "strengths": 2-5 specific, evidence-grounded strengths. Reference actual answers or resume
  content, not generic praise (e.g. "Demonstrated hands-on Redis experience with clear reasoning
  about TTL and cache invalidation" not "Good technical skills").
- "weaknesses": 2-5 specific, evidence-grounded areas for improvement, grounded in the actual
  evaluation reasoning provided (low-scoring dimensions, missing skills, weak delivery metrics).
  Be honest and specific, not softened into vagueness.
- "recommended_learning_path": 2-5 concrete, actionable next steps tied to the missing/weak
  skills identified (e.g. "Build a small project using Docker to containerize an existing API"
  rather than just "Learn Docker").
- "topics_to_practice": 3-6 short topic labels for further interview practice, informed by
  weak/missing skills and any low-scoring evaluation dimensions.
- "interview_summary": 3-5 sentences giving an overall narrative assessment of the interview
  performance, written for a hiring manager -- reference the resume match, technical performance,
  and communication/delivery observations together into one coherent picture.
- Ground every claim in the data provided. Never invent skills, experience, or answer content
  not present in the input.
"""


def _extract_scores(
    match_result: MatchResult | None,
    evaluation_summary: EvaluationSessionSummary | None,
    cv_summary: CVSessionSummary | None,
    speech_summary: SpeechSessionSummary | None,
    overall: OverallScoreResult,
) -> dict[str, float | None]:
    # Eye contact and confidence are reported but intentionally NOT part of
    # Module 9's weighted overall_score -- they're additional diagnostic
    # metrics the spec asks the report to surface, not double-counted into
    # the headline number.
    eye_contact_score = cv_summary.eye_contact_percentage if cv_summary else None

    confidence_components = [
        v
        for v in [
            speech_summary.average_confidence_score if speech_summary else None,
            evaluation_summary.average_confidence if evaluation_summary else None,
        ]
        if v is not None
    ]
    confidence_score = (
        round(sum(confidence_components) / len(confidence_components), 1)
        if confidence_components
        else None
    )

    return {
        "resume_match_score": overall.resume_match.score,
        "technical_score": overall.technical_answers.score,
        "communication_score": overall.communication.score,
        "confidence_score": confidence_score,
        "eye_contact_score": eye_contact_score,
        "attention_score": overall.computer_vision.score,
        "behavioral_score": overall.behavioral_performance.score,
        "speech_quality_score": overall.speech_analysis.score,
    }


def generate_report(
    session_id: str,
    resume: ParsedResume,
    jd: ParsedJobDescription,
    match_result: MatchResult | None,
    evaluations: list[AnswerEvaluation],
    evaluation_summary: EvaluationSessionSummary | None,
    cv_summary: CVSessionSummary | None,
    speech_summary: SpeechSessionSummary | None,
    overall: OverallScoreResult,
) -> InterviewReport:
    scores = _extract_scores(match_result, evaluation_summary, cv_summary, speech_summary, overall)
    missing_skills = match_result.missing_skills if match_result else []

    user_prompt = (
        f"RESUME:\n{resume.model_dump_json(indent=2)}\n\n"
        f"JOB DESCRIPTION:\n{jd.model_dump_json(indent=2)}\n\n"
        f"MATCH ANALYSIS:\n{match_result.model_dump_json(indent=2) if match_result else 'Not available.'}\n\n"
        f"PER-ANSWER EVALUATIONS:\n"
        + (
            "\n".join(
                f"Q{e.turn_number}: {e.question}\n  Overall summary: {e.overall_summary}\n"
                f"  Dimension scores: technical_accuracy={e.technical_accuracy.score if e.technical_accuracy else 'N/A'}, "
                f"depth_of_knowledge={e.depth_of_knowledge.score if e.depth_of_knowledge else 'N/A'}, "
                f"communication={e.communication.score}, confidence={e.confidence.score}"
                for e in evaluations
            )
            if evaluations
            else "Not available."
        )
        + f"\n\nCOMPUTER VISION SUMMARY:\n{cv_summary.model_dump_json(indent=2) if cv_summary else 'Not available.'}\n\n"
        f"SPEECH SUMMARY:\n{speech_summary.model_dump_json(indent=2) if speech_summary else 'Not available.'}\n\n"
        f"OVERALL SCORE BREAKDOWN:\n{overall.model_dump_json(indent=2)}\n"
    )

    llm_result = get_llm_json(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)

    return InterviewReport(
        session_id=session_id,
        **scores,
        overall_score=overall.overall_score,
        strengths=llm_result.get("strengths", []),
        weaknesses=llm_result.get("weaknesses", []),
        missing_skills=missing_skills,
        recommended_learning_path=llm_result.get("recommended_learning_path", []),
        topics_to_practice=llm_result.get("topics_to_practice", []),
        interview_summary=llm_result.get("interview_summary", ""),
        performance_breakdown=overall,
    )
