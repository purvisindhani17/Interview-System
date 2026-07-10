"""
Resume-vs-JD comparison orchestration (Step 3 of the interview workflow).

Design principle: the headline percentage is computed deterministically
(skill overlap + TF-IDF semantic similarity), never guessed by the LLM.
The LLM is used only for qualitative judgment that benefits from language
understanding: refining strong/weak skill labels and deciding what topics
an interviewer should focus on given the gaps. This keeps the numeric
score reproducible while still getting LLM-quality reasoning about *why*.
"""

from app.modules.job_parser.schema import ParsedJobDescription
from app.modules.match_engine.schema import MatchResult
from app.modules.match_engine.semantic_similarity import compute_semantic_similarity
from app.modules.match_engine.skill_matcher import compute_skill_overlap
from app.modules.resume_parser.schema import ParsedResume
from app.utils.llm_client import get_llm_json

# Weighted blend of the two deterministic signals into one headline percentage.
SKILL_OVERLAP_WEIGHT = 0.65
SEMANTIC_SIMILARITY_WEIGHT = 0.35

SYSTEM_PROMPT = """You are an expert technical interviewer's assistant. You will be given:
- A candidate's structured resume data
- A structured job description
- A precomputed list of matched/missing required and preferred skills (from exact
  and fuzzy string matching -- treat this as a reliable starting point, not the final word)

Return ONLY a single valid JSON object -- no markdown fences, no commentary -- with this shape:
{
  "strong_skills": [string],
  "missing_skills": [string],
  "weak_skills": [string],
  "interview_focus_topics": [string],
  "summary": string
}

Rules:
- "strong_skills": skills the candidate clearly has strong, well-evidenced experience with,
  relevant to this JD. Start from "matched_required"/"matched_preferred" but you may add a
  skill if the resume's project/experience descriptions clearly demonstrate it even if the
  exact keyword match missed it (e.g. "built a caching layer with Redis" satisfies "Redis").
- "missing_skills": required or preferred JD skills with no evidence anywhere in the resume.
  Start from "missing_required"/"missing_preferred" but remove any you find clear evidence for.
- "weak_skills": skills the candidate lists or briefly mentions but with limited depth of
  evidence (e.g. listed as a skill keyword but never appears in any project/experience description).
- "interview_focus_topics": 3-6 topics the interviewer should prioritize testing, based on
  missing skills, weak skills, and JD responsibilities. Use concrete topic names
  (e.g. "System Design", "Database Indexing", "React State Management"), not full sentences.
- "summary": 2-3 sentence plain-English assessment of overall fit, written for a hiring manager.
- Do not invent skills or experience not present in the resume. Never omit a key.
"""


def compare_resume_to_job(resume: ParsedResume, jd: ParsedJobDescription) -> MatchResult:
    overlap = compute_skill_overlap(
        resume_skills=resume.skills + resume.technologies,
        required_skills=jd.required_skills,
        preferred_skills=jd.preferred_skills,
    )
    semantic_score = compute_semantic_similarity(resume, jd)

    resume_match_percentage = round(
        (overlap["overlap_percentage"] * SKILL_OVERLAP_WEIGHT)
        + (semantic_score * SEMANTIC_SIMILARITY_WEIGHT),
        1,
    )

    user_prompt = (
        f"RESUME:\n{resume.model_dump_json(indent=2)}\n\n"
        f"JOB DESCRIPTION:\n{jd.model_dump_json(indent=2)}\n\n"
        f"PRECOMPUTED SKILL OVERLAP:\n"
        f"matched_required: {overlap['matched_required']}\n"
        f"missing_required: {overlap['missing_required']}\n"
        f"matched_preferred: {overlap['matched_preferred']}\n"
        f"missing_preferred: {overlap['missing_preferred']}\n"
    )

    llm_result = get_llm_json(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)

    return MatchResult(
        resume_match_percentage=resume_match_percentage,
        skill_overlap_percentage=overlap["overlap_percentage"],
        semantic_similarity_percentage=semantic_score,
        strong_skills=llm_result.get("strong_skills", []),
        missing_skills=llm_result.get("missing_skills", []),
        weak_skills=llm_result.get("weak_skills", []),
        interview_focus_topics=llm_result.get("interview_focus_topics", []),
        summary=llm_result.get("summary", ""),
    )
