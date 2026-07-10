"""
Resume parsing orchestration.

Flow:
    PDF file -> raw text (pdf_extractor) -> structured JSON (LLM) -> ParsedResume

The LLM call is isolated behind app.utils.llm_client.get_llm_json so this
module doesn't care whether it's talking to OpenAI or another provider.
"""

from app.modules.resume_parser.pdf_extractor import extract_text_from_pdf
from app.modules.resume_parser.schema import ParsedResume
from app.utils.llm_client import get_llm_json

SYSTEM_PROMPT = """You are a precise resume parser. You will be given raw text
extracted from a candidate's resume PDF. Extract the following fields and
return ONLY a single valid JSON object -- no markdown fences, no commentary.

Required JSON shape:
{
  "name": string,
  "email": string,
  "phone": string,
  "skills": [string],
  "experience": [{"company": string, "role": string, "duration": string, "description": string}],
  "projects": [{"name": string, "description": string, "technologies": [string]}],
  "education": [{"institution": string, "degree": string, "year": string}],
  "technologies": [string],
  "certifications": [string],
  "total_experience_years": number or null
}

Rules:
- If a field cannot be found, use an empty string, empty list, or null as appropriate. Never omit a key.
- "skills" = soft/technical skill keywords mentioned generally (e.g. "Python", "Leadership").
- "technologies" = tools/frameworks/platforms distinct from core skills (e.g. "Docker", "PostgreSQL", "AWS").
  Some overlap between skills and technologies is fine.
- "total_experience_years" should be your best numeric estimate based on dates in the experience section.
- Do not invent information that is not present in the resume text.
"""


def parse_resume_text(raw_text: str) -> ParsedResume:
    """Send extracted resume text to the LLM and validate the structured result."""
    structured = get_llm_json(system_prompt=SYSTEM_PROMPT, user_prompt=raw_text)
    return ParsedResume(**structured)


def parse_resume_pdf(filepath: str) -> ParsedResume:
    """Full pipeline: PDF path -> ParsedResume."""
    raw_text = extract_text_from_pdf(filepath)
    return parse_resume_text(raw_text)
