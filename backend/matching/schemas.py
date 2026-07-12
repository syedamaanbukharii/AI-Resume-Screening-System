"""Schemas for match scoring: per-factor evidence and composite results.

Every sub-score ships with the evidence that produced it. The composite is a
deterministic weighted sum; the evidence is what makes a bare float defensible
to a recruiter and auditable under review.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SkillMatchEvidence(BaseModel):
    """Evidence for a single matched (or missing) skill."""

    skill: str
    match_type: str  # 'exact' | 'semantic' | 'missing'
    similarity: float | None = None  # populated for semantic matches
    weight: float = 1.0  # required=1.0, preferred<1.0


class SkillScore(BaseModel):
    """Skill sub-score with its full evidence trail."""

    score: float
    matched_exact: list[SkillMatchEvidence] = Field(default_factory=list)
    matched_semantic: list[SkillMatchEvidence] = Field(default_factory=list)
    missing_required: list[str] = Field(default_factory=list)
    rationale: str = ""


class ExperienceScore(BaseModel):
    """Experience sub-score with the reasoning behind it."""

    score: float
    candidate_years: float | None
    required_years: int | None
    rationale: str = ""


class EducationScore(BaseModel):
    """Education sub-score with matched degree evidence."""

    score: float
    highest_degree: str | None
    required_level: str | None
    field_aligned: bool
    rationale: str = ""


class SemanticScore(BaseModel):
    """Full-document semantic similarity sub-score."""

    score: float
    cosine_similarity: float | None
    rationale: str = ""


class CertificationScore(BaseModel):
    """Certification bonus sub-score."""

    score: float
    matched: list[str] = Field(default_factory=list)
    rationale: str = ""


class MatchResult(BaseModel):
    """The complete, explainable scoring result for one candidate on one job."""

    overall_score: float
    skill: SkillScore
    experience: ExperienceScore
    education: EducationScore
    semantic: SemanticScore
    certification: CertificationScore
    weights_used: dict[str, float]

    def sub_scores(self) -> dict[str, float]:
        """Return the five raw sub-scores keyed by factor."""
        return {
            "skill": self.skill.score,
            "experience": self.experience.score,
            "education": self.education.score,
            "semantic": self.semantic.score,
            "certification": self.certification.score,
        }
