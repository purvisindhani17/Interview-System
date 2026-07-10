"""
Text extraction for job descriptions.

Unlike resumes, a JD is usually pasted as plain text -- but we also support
uploading a .pdf or .txt file for convenience, since some companies only
share JDs as PDF attachments. This module normalizes both paths into plain
text before handing off to parser.py.
"""

from app.modules.resume_parser.pdf_extractor import ResumeExtractionError, extract_text_from_pdf


class JobDescriptionExtractionError(Exception):
    """Raised when no usable text can be obtained from the uploaded JD file."""


def extract_text_from_file(filepath: str, content_type: str) -> str:
    """Extract plain text from an uploaded JD file (PDF or plain text)."""
    if content_type == "application/pdf":
        try:
            return extract_text_from_pdf(filepath)
        except ResumeExtractionError as e:
            # Re-raise under the job_parser's own error type so callers only
            # need to catch one exception type per module.
            raise JobDescriptionExtractionError(str(e)) from e

    if content_type in ("text/plain", "text/markdown") or filepath.endswith((".txt", ".md")):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()
        if not text:
            raise JobDescriptionExtractionError("The uploaded file appears to be empty.")
        return text

    raise JobDescriptionExtractionError(
        f"Unsupported file type '{content_type}'. Please upload a PDF or .txt file, "
        "or paste the job description as text instead."
    )
