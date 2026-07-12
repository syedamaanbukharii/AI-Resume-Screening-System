"""Weighted scoring engine composing five explainable sub-scores."""

from __future__ import annotations

from backend.embeddings.base import BaseEmbedder
from backend.matching.education_matcher import score_education
from backend.matching.experience_matcher import score_experience
from backend.matching.schemas import (
    CertificationScore,
    MatchResult,
    SemanticScore,
)
from backend.matching.skill_matcher import score_skills
from backend.resume.schemas import CandidateProfile

_DEFAULT_WEIGHTS = {
    "skill": 0.35,
    "experience": 0.25,
    "education": 0.15,
    "semantic": 0.15,
    "certification": 0.10,
}


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two equal-length vectors."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = sum(x * x for x in a) ** 0.5 or 1.0
    nb = sum(y * y for y in b) ** 0.5 or 1.0
    return dot / (na * nb)


def _score_semantic(
    resume_embedding: list[float] | None, job_embedding: list[float] | None
) -> SemanticScore:
    """Score full-document semantic similarity from precomputed embeddings.

    Cosine in [-1, 1] is rescaled to [0, 1]. Missing either embedding yields a
    neutral 0.5 so the composite is not silently biased by absent vectors.
    """
    if resume_embedding is None or job_embedding is None:
        return SemanticScore(
            score=0.5,
            cosine_similarity=None,
            rationale="Embedding unavailable on one side; neutral score applied.",
        )
    if len(resume_embedding) != len(job_embedding):
        return SemanticScore(
            score=0.5,
            cosine_similarity=None,
            rationale="Embedding dimension mismatch; neutral score applied.",
        )
    cos = _cosine(resume_embedding, job_embedding)
    score = max(min((cos + 1.0) / 2.0, 1.0), 0.0)
    return SemanticScore(
        score=round(score, 4),
        cosine_similarity=round(cos, 4),
        rationale=f"Full-document cosine similarity {cos:.3f}.",
    )


def _score_certifications(
    candidate_certs: list[str], required_skills: list[str], preferred_skills: list[str]
) -> CertificationScore:
    """Score relevant certifications as a bonus factor.

    A certification is "relevant" if any JD skill term appears in it. Score is
    the fraction of JD skill areas with at least one matching certification,
    capped at 1.0. Absence of certifications is not penalized below zero.
    """
    jd_terms = [t.lower() for t in (required_skills + preferred_skills) if t.strip()]
    if not jd_terms:
        has_any = 1.0 if candidate_certs else 0.0
        return CertificationScore(
            score=has_any,
            matched=candidate_certs,
            rationale="No JD skills to match certifications against.",
        )

    matched: list[str] = []
    for cert in candidate_certs:
        low = cert.lower()
        if any(term in low for term in jd_terms):
            matched.append(cert)

    denom = min(len(jd_terms), 5)  # cap denominator so a few relevant certs score well
    score = min(len(matched) / denom, 1.0) if denom else 0.0
    return CertificationScore(
        score=round(score, 4),
        matched=matched,
        rationale=f"{len(matched)} relevant certification(s) matched JD skill areas.",
    )


async def compute_match(
    *,
    profile: CandidateProfile,
    resume_embedding: list[float] | None,
    job_embedding: list[float] | None,
    required_skills: list[str],
    preferred_skills: list[str],
    min_experience_years: int | None,
    education_level: str | None,
    job_field_terms: list[str] | None,
    weights: dict[str, float] | None,
    embedder: BaseEmbedder | None,
) -> MatchResult:
    """Compute the full explainable match result for a candidate on a job.

    All five sub-scores are normalized to [0, 1] on the SAME scale before the
    weighted sum, so the composite is meaningful and comparable across
    candidates. Weights default to the spec values and are overridable per job.
    """
    w = dict(_DEFAULT_WEIGHTS)
    if weights:
        w.update({k: v for k, v in weights.items() if k in _DEFAULT_WEIGHTS})
    weight_sum = sum(w.values()) or 1.0
    w = {k: v / weight_sum for k, v in w.items()}  # renormalize defensively

    candidate_skills = list(
        dict.fromkeys(profile.technical_skills + profile.tools_and_frameworks)
    )

    skill = await score_skills(
        candidate_skills=candidate_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        embedder=embedder,
    )
    experience = score_experience(
        candidate_years=profile.total_years_experience,
        required_years=min_experience_years,
    )
    education = score_education(
        education=profile.education,
        required_level=education_level,
        job_field_terms=job_field_terms,
    )
    semantic = _score_semantic(resume_embedding, job_embedding)
    certification = _score_certifications(
        profile.certifications, required_skills, preferred_skills
    )

    overall = (
        w["skill"] * skill.score
        + w["experience"] * experience.score
        + w["education"] * education.score
        + w["semantic"] * semantic.score
        + w["certification"] * certification.score
    )

    return MatchResult(
        overall_score=round(overall, 4),
        skill=skill,
        experience=experience,
        education=education,
        semantic=semantic,
        certification=certification,
        weights_used=w,
    )
