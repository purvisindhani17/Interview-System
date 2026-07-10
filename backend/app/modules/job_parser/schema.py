"""
Pydantic schema for structured job description data.

Mirrors the resume_parser schema pattern: this is the contract that
Module 3 (resume-vs-JD comparison) and the interview engine will consume.
"""

from pydantic import BaseModel, Field


class ParsedJobDescription(BaseModel):
    jd_id: str | None = None  # populated by the API layer, not by the LLM parser
    job_title: str = ""
    company: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    experience_required_years: float | None = None
    seniority_level: str = ""  # e.g. "Junior", "Mid", "Senior", "Lead" -- best-effort inference

    class Config:
        json_schema_extra = {
            "example": {
                "job_title": "Backend Engineer",
                "company": "Acme Corp",
                "required_skills": ["Python", "FastAPI", "REST APIs"],
                "preferred_skills": ["Docker", "Redis"],
                "responsibilities": [
                    "Design and maintain internal APIs",
                    "Collaborate with frontend engineers on API contracts",
                ],
                "technologies": ["PostgreSQL", "Docker", "AWS"],
                "experience_required_years": 3.0,
                "seniority_level": "Mid",
            }
        }
