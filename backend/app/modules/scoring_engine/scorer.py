"""
Overall weighted interview score (Step "Scoring" of the spec).

Pure aggregation over already-computed results from earlier modules --
no I/O, no LLM, fully unit-testable with synthetic summary objects.
Weights match the spec exactly:
  Resume Match 15% | Technical Answers 35% | Communication 15% |
  Computer Vision Metrics 15% | Speech Analysis 10% | Behavioral Performance 10%

If a category's underlying data isn't available (e.g. no CV frames were
recorded, or no behavioral questions came up in the interview), that
category is excluded and the remaining weights are renormalized to sum
to 1 -- same pattern used throughout this project (match_engine,
evaluation_engine) rather than penalizing a candidate for a component
that was never run.
"""

from app.modules.cv_analysis.schema import CVSessionSummary
from app.modules.evaluation_engine.schema import EvaluationSessionSummary
from app.modules.match_engine.schema import MatchResult
from app.modules.scoring_engine.schema import CategoryScore, OverallScoreResult
from app.modules.speech_analysis.schema import SpeechSessionSummary

CATEGORY_WEIGHTS = {
    "resume_match": 0.15,
    "technical_answers": 0.35,
    "communication": 0.15,
    "computer_vision": 0.15,
    "speech_analysis": 0.10,
    "behavioral_performance": 0.10,
}


def _average(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def compute_overall_score(
    session_id: str,
    match_result: MatchResult | None,
    evaluation_summary: EvaluationSessionSummary | None,
    cv_summary: CVSessionSummary | None,
    speech_summary: SpeechSessionSummary | None,
) -> OverallScoreResult:
    raw_scores: dict[str, float | None] = {
        "resume_match": match_result.resume_match_percentage if match_result else None,
        "technical_answers": (
            _average(
                [
                    v
                    for v in [
                        evaluation_summary.average_technical_accuracy,
                        evaluation_summary.average_depth_of_knowledge,
                        evaluation_summary.average_problem_solving,
                    ]
                    if v is not None
                ]
            )
            if evaluation_summary
            else None
        ),
        "communication": evaluation_summary.average_communication if evaluation_summary else None,
        "computer_vision": cv_summary.average_attention_score if cv_summary else None,
        "speech_analysis": (
            speech_summary.average_communication_quality_score if speech_summary else None
        ),
        "behavioral_performance": (
            _average(
                [
                    v
                    for v in [
                        evaluation_summary.average_behavioral_skills,
                        evaluation_summary.average_star_method_adherence,
                    ]
                    if v is not None
                ]
            )
            if evaluation_summary
            else None
        ),
    }

    categories = {
        name: CategoryScore(score=score, weight=CATEGORY_WEIGHTS[name], available=score is not None)
        for name, score in raw_scores.items()
    }

    available_weight_total = sum(CATEGORY_WEIGHTS[name] for name, cat in categories.items() if cat.available)

    if available_weight_total == 0:
        overall = 0.0
    else:
        weighted_sum = sum(
            cat.score * CATEGORY_WEIGHTS[name] for name, cat in categories.items() if cat.available
        )
        overall = round(weighted_sum / available_weight_total, 1)

    return OverallScoreResult(
        session_id=session_id,
        resume_match=categories["resume_match"],
        technical_answers=categories["technical_answers"],
        communication=categories["communication"],
        computer_vision=categories["computer_vision"],
        speech_analysis=categories["speech_analysis"],
        behavioral_performance=categories["behavioral_performance"],
        overall_score=overall,
        categories_included=[name for name, cat in categories.items() if cat.available],
        categories_missing=[name for name, cat in categories.items() if not cat.available],
    )
