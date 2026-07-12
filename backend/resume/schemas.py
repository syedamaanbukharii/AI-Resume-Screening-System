"""Pydantic schemas for the structured candidate profile the LLM extracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExperienceEntry(BaseModel):
    """A single employment record."""

    company: str
    title: str
    start_date: str | None = None
    end_date: str | None = None  # None denotes "Present"
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    """A single education record."""

    institution: str
    degree: str
    field: str | None = None
    graduation_year: int | None = None
    gpa: float | None = None


class ProjectEntry(BaseModel):
    """A single project record."""

    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    url: str | None = None


class CandidateProfile(BaseModel):
    """The full structured profile extracted from a resume in one LLM call."""

    full_name: str
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    summary: str | None = None

    technical_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    tools_and_frameworks: list[str] = Field(default_factory=list)

    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)

    total_years_experience: float | None = None

    def to_embedding_text(self) -> str:
        """Concatenate salient fields into a single string for embedding."""
        parts: list[str] = [self.full_name]
        if self.summary:
            parts.append(self.summary)
        parts.append(" ".join(self.technical_skills))
        parts.append(" ".join(self.tools_and_frameworks))
        for exp in self.experience:
            parts.append(f"{exp.title} at {exp.company}. {exp.description or ''}")
            parts.append(" ".join(exp.technologies))
        for edu in self.education:
            parts.append(f"{edu.degree} {edu.field or ''} {edu.institution}")
        for proj in self.projects:
            parts.append(f"{proj.name}. {proj.description or ''}")
            parts.append(" ".join(proj.technologies))
        parts.extend(self.certifications)
        return "\n".join(p for p in parts if p and p.strip())
