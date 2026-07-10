"""
Pydantic schema for structured resume data.

This is the contract between the resume parser and every downstream
module (JD matching, interview engine, scoring). Keeping it strongly
typed means later modules get autocomplete + validation instead of
guessing dict keys.
"""

from pydantic import BaseModel, Field


class ExperienceEntry(BaseModel):
    company: str = ""
    role: str = ""
    duration: str = ""
    description: str = ""


class ProjectEntry(BaseModel):
    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    institution: str = ""
    degree: str = ""
    year: str = ""


class ParsedResume(BaseModel):
    resume_id: str | None = None  # populated by the API layer, not by the LLM parser
    name: str = ""
    email: str = ""
    phone: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    total_experience_years: float | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "+1-555-123-4567",
                "skills": ["Python", "FastAPI", "React"],
                "experience": [
                    {
                        "company": "Acme Corp",
                        "role": "Backend Engineer",
                        "duration": "2022 - Present",
                        "description": "Built internal APIs serving 1M+ requests/day.",
                    }
                ],
                "projects": [
                    {
                        "name": "AI Interview System",
                        "description": "A voice-based mock interview platform.",
                        "technologies": ["FastAPI", "OpenCV", "Whisper"],
                    }
                ],
                "education": [
                    {"institution": "State University", "degree": "B.Tech CSE", "year": "2022"}
                ],
                "technologies": ["Docker", "PostgreSQL"],
                "certifications": ["AWS Certified Developer"],
                "total_experience_years": 2.5,
            }
        }
