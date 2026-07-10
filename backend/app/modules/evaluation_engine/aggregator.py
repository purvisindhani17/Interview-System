"""
Deterministic aggregation for Module 8 evaluations.

Same principle as match_engine's scoring and difficulty_engine's state
machine: once the LLM has supplied the per-dimension judgment calls, the
arithmetic that combines them into a single number is fixed code, not
another LLM guess -- so the same set of dimension scores always produces
the same overall_score.
"""

from app.modules.evaluation_engine.schema import AnswerEvaluation, EvaluationSessionSummary

# Relative importance of each dimension when present. Weights for
# dimensions that don't apply to a given answer (e.g. STAR method on a
# purely technical question) are dropped and the remaining weights are
# renormalized to sum to 1, so the overall_score stays on a consistent
# 0-100 scale regardless of question type.
DIMENSION_WEIGHTS = {
    "technical_accuracy": 0.20,
    "depth_of_knowledge": 0.15,
    "problem_solving": 0.15,
    "behavioral_skills": 0.15,
    "star_method_adherence": 0.10,
    "communication": 0.10,
    "confidence": 0.05,
    "explanation_quality": 0.10,
}


def compute_overall_score(evaluation: AnswerEvaluation) -> float:
    weighted_sum = 0.0
    total_weight = 0.0

    for dimension_name, weight in DIMENSION_WEIGHTS.items():
        dimension = getattr(evaluation, dimension_name)
        if dimension is not None:
            weighted_sum += dimension.score * weight
            total_weight += weight

    if total_weight == 0:
        return 0.0

    return round(weighted_sum / total_weight, 1)


def summarize_session(session_id: str, evaluations: list[AnswerEvaluation]) -> EvaluationSessionSummary:
    if not evaluations:
        return EvaluationSessionSummary(session_id=session_id, turns_evaluated=0)

    def avg(values: list[float]) -> float | None:
        return round(sum(values) / len(values), 1) if values else None

    technical = [e.technical_accuracy.score for e in evaluations if e.technical_accuracy]
    depth = [e.depth_of_knowledge.score for e in evaluations if e.depth_of_knowledge]
    problem_solving = [e.problem_solving.score for e in evaluations if e.problem_solving]
    behavioral = [e.behavioral_skills.score for e in evaluations if e.behavioral_skills]
    star = [e.star_method_adherence.score for e in evaluations if e.star_method_adherence]
    communication = [e.communication.score for e in evaluations]
    confidence = [e.confidence.score for e in evaluations]
    explanation = [e.explanation_quality.score for e in evaluations]
    overall = [e.overall_score for e in evaluations]

    return EvaluationSessionSummary(
        session_id=session_id,
        turns_evaluated=len(evaluations),
        average_technical_accuracy=avg(technical),
        average_depth_of_knowledge=avg(depth),
        average_problem_solving=avg(problem_solving),
        average_behavioral_skills=avg(behavioral),
        average_star_method_adherence=avg(star),
        average_communication=avg(communication) or 0.0,
        average_confidence=avg(confidence) or 0.0,
        average_explanation_quality=avg(explanation) or 0.0,
        average_overall_score=avg(overall) or 0.0,
    )
