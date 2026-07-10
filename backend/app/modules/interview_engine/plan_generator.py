"""
Interview plan generation (Step 4 of the workflow).

Flow:
    ParsedResume + ParsedJobDescription + MatchResult -> LLM -> InterviewPlan

Unlike the deterministic scoring in match_engine, this module is entirely
LLM-driven by design: deciding *what to ask* and *how to sequence a
conversation* is a judgment call that benefits from language understanding,
not something to hard-code into if/else rules. The plan produced here is
the starting strategy for Module 5's live, adaptive interview loop.
"""

from app.modules.interview_engine.schema import InterviewPlan
from app.modules.job_parser.schema import ParsedJobDescription
from app.modules.match_engine.schema import MatchResult
from app.modules.resume_parser.schema import ParsedResume
from app.utils.llm_client import get_llm_json

SYSTEM_PROMPT = """You are an expert technical interviewer designing an interview strategy
before the interview begins. You will be given a candidate's structured resume, a
structured job description, and a structured resume-vs-JD match analysis (strong
skills, missing skills, weak skills, and suggested focus topics).

Return ONLY a single valid JSON object -- no markdown fences, no commentary -- with this shape:
{
  "interview_strategy_summary": string,
  "starting_difficulty": "easy" | "medium" | "hard",
  "opening_questions": [string],
  "topic_priorities": [{"topic": string, "importance": "high" | "medium" | "low", "reason": string}],
  "project_follow_ups": [{"project_name": string, "questions": [string], "reason": string}],
  "sequence": [string],
  "estimated_question_count": integer
}

Rules:
- "interview_strategy_summary": 2-4 sentences explaining your overall approach for this
  specific candidate and role -- reference their actual strengths/gaps, not generic advice.
- "starting_difficulty": base this on the match analysis. Strong match (resume_match_percentage
  roughly 75+) with few missing skills -> "hard". Weak match or many missing/weak skills -> "easy".
  Otherwise -> "medium".
- "opening_questions": 1-3 warm, low-pressure questions to open the interview and confirm the
  candidate's headline experience before going deeper.
- "topic_priorities": derive from missing_skills, weak_skills, and interview_focus_topics in the
  match analysis, plus JD responsibilities. Order matters -- put the most important topic first.
- "project_follow_ups": pick specific named projects from the candidate's resume (only ones that
  actually appear in the resume data -- never invent a project) that are most relevant to the JD
  or that best evidence a skill worth probing further. 1-3 targeted follow-up questions per project.
- "sequence": a short ordered list of phase names describing how the interview should flow overall
  (e.g. ["Warm-up", "Core technical skills", "Project deep-dive", "Gap probing", "Behavioral (STAR)", "Wrap-up"]).
- "estimated_question_count": a reasonable total number of questions for a focused technical
  interview given the plan's scope (typically 8-15).
- Never invent skills, projects, or experience not present in the input data.
"""


def generate_interview_plan(
    resume: ParsedResume, jd: ParsedJobDescription, match: MatchResult
) -> InterviewPlan:
    user_prompt = (
        f"RESUME:\n{resume.model_dump_json(indent=2)}\n\n"
        f"JOB DESCRIPTION:\n{jd.model_dump_json(indent=2)}\n\n"
        f"MATCH ANALYSIS:\n{match.model_dump_json(indent=2)}\n"
    )

    llm_result = get_llm_json(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)
    return InterviewPlan(**llm_result)
