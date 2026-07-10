"""
Raw text extraction from resume PDFs.

Kept separate from parser.py so the "get text out of a PDF" concern
never mixes with the "turn text into structured JSON via LLM" concern.
This also makes it trivial to unit-test extraction without needing an
LLM API key.
"""

import pdfplumber


class ResumeExtractionError(Exception):
    """Raised when a PDF's text cannot be extracted (empty, corrupted, scanned-image-only, etc.)."""


def extract_text_from_pdf(filepath: str) -> str:
    """Extract raw text from every page of a PDF resume.

    Raises ResumeExtractionError if no extractable text is found (e.g. the
    PDF is a scanned image with no text layer -- OCR is out of scope for
    this portfolio project but the error message says so explicitly).
    """
    pages_text: list[str] = []

    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

    full_text = "\n".join(pages_text).strip()

    if not full_text:
        raise ResumeExtractionError(
            "No extractable text found in this PDF. It may be a scanned "
            "image without a text layer. Try a text-based PDF export of the resume."
        )

    return full_text
