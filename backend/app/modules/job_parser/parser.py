"""
Job description parsing orchestration.

Flow:
    raw JD text (pasted or extracted from an uploaded file) -> structured JSON (LLM) -> ParsedJobDescription

Same pattern as resume_parser/parser.py: the LLM call goes through
app.utils.llm_client so provider swaps only touch one file.
"""

from app.modules.job_parser.schema import ParsedJobDescription
from app.utils.llm_client import get_llm_json

SYSTEM_PROMPT = """You are a precise job description parser. You will be given the raw text
of a job posting. Extract the following fields and return ONLY a single valid
JSON object -- no markdown fences, no commentary.

Required JSON shape:
{
  "job_title": string,
  "company": string,
  "required_skills": [string],
  "preferred_skills": [string],
  "responsibilities": [string],
  "technologies": [string],
  "experience_required_years": number or null,
  "seniority_level": string
}

Rules:
- "required_skills" = must-have skills explicitly stated as required/mandatory.
- "preferred_skills" = "nice to have", "bonus", "preferred", or "plus" skills.
- "responsibilities" = the core day-to-day duties listed in the posting, kept as
  short individual bullet strings (not full paragraphs).
- "technologies" = specific tools/frameworks/platforms mentioned (e.g. "Docker",
  "Kubernetes", "PostgreSQL", "AWS"). Distinct from general skills where possible,
  but some overlap is fine.
- "experience_required_years" should be your best numeric estimate from phrases
  like "3+ years" or "5-7 years experience". Use null if not stated.
- "seniority_level" should be your best single-word-or-short-phrase inference
  (e.g. "Junior", "Mid", "Senior", "Lead", "Staff") based on title and requirements.
  Use an empty string if it truly cannot be inferred.
- If a field cannot be found, use an empty string, empty list, or null as
  appropriate. Never omit a key. Do not invent information not present in the text.
"""


def parse_job_description_text(raw_text: str) -> ParsedJobDescription:
    """Send raw JD text to the LLM and validate the structured result."""
    structured = get_llm_json(system_prompt=SYSTEM_PROMPT, user_prompt=raw_text)
    return ParsedJobDescription(**structured)
