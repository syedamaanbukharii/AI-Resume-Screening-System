"""Unit tests for the matching engine (hermetic — no external services)."""

from __future__ import annotations

import pytest

from backend.matching.education_matcher import score_education
from backend.matching.engine import compute_match
from backend.matching.experience_matcher import score_experience
from backend.matching.skill_matcher import score_skills
from backend.resume.schemas import CandidateProfile, EducationEntry


@pytest.mark.asyncio
async def test_skill_exact_full_credit() -> None:
    """All required skills matched lexically scores 1.0."""
    s = await score_skills(
        candidate_skills=["python", "kubernetes"],
        required_skills=["python", "kubernetes"],
        preferred_skills=[],
        embedder=None,
    )
    assert s.score == 1.0
    assert not s.missing_required


@pytest.mark.asyncio
async def test_skill_missing_required_recorded() -> None:
    """An unmatched required skill lowers score and is recorded."""
    s = await score_skills(
        candidate_skills=["python"],
        required_skills=["python", "kubernetes"],
        preferred_skills=[],
        embedder=None,
    )
    assert s.score == pytest.approx(0.5)
    assert "kubernetes" in s.missing_required


@pytest.mark.asyncio
async def test_skill_semantic_fallback_discounted() -> None:
    """A semantic-only match counts at a discount, with evidence."""

    class FakeEmb:
        dimension = 4

        async def embed_batch(self, texts: list[str]) -> list[list[float]]:
            table = {
                "recommendation systems": [1.0, 0.0, 0.0, 0.0],
                "recsys": [0.95, 0.05, 0.0, 0.0],
            }
            return [table.get(t.lower(), [0.0, 0.0, 0.0, 1.0]) for t in texts]

        async def embed(self, text: str) -> list[float]:
            return (await self.embed_batch([text]))[0]

    s = await score_skills(
        candidate_skills=["recommendation systems"],
        required_skills=["recsys"],
        preferred_skills=[],
        embedder=FakeEmb(),
    )
    assert s.matched_semantic
    assert 0.6 <= s.score < 1.0  # discounted below a full exact match


def test_experience_saturates() -> None:
    """Experience at/above the minimum scores 1.0; below scales linearly."""
    assert score_experience(candidate_years=10, required_years=5).score == 1.0
    assert score_experience(candidate_years=2, required_years=5).score == pytest.approx(0.4)
    assert score_experience(candidate_years=None, required_years=5).score == 0.5
    assert score_experience(candidate_years=3, required_years=None).score == 1.0


def test_education_level_and_field() -> None:
    """A higher degree satisfies a lower requirement; field alignment adds."""
    edu = [EducationEntry(institution="MIT", degree="master of science", field="computer science")]
    high = score_education(
        education=edu, required_level="bachelor", job_field_terms=["computer science"]
    )
    assert high.score == 1.0
    low = score_education(
        education=[EducationEntry(institution="X", degree="bachelor of arts", field="history")],
        required_level="master",
        job_field_terms=["computer science"],
    )
    assert low.score < high.score


@pytest.mark.asyncio
async def test_composite_ranks_strong_over_weak() -> None:
    """The weighted composite separates a strong fit from a weak one."""
    strong = CandidateProfile(
        full_name="Strong",
        technical_skills=["python", "pytorch", "kubernetes"],
        total_years_experience=6,
        education=[EducationEntry(institution="MIT", degree="master of science")],
    )
    weak = CandidateProfile(
        full_name="Weak",
        technical_skills=["excel"],
        total_years_experience=1,
        education=[EducationEntry(institution="X", degree="bachelor of arts")],
    )
    args = dict(
        resume_embedding=None,
        job_embedding=None,
        required_skills=["python", "pytorch"],
        preferred_skills=["kubernetes"],
        min_experience_years=5,
        education_level="bachelor",
        job_field_terms=None,
        weights=None,
        embedder=None,
    )
    strong_res = await compute_match(profile=strong, **args)
    weak_res = await compute_match(profile=weak, **args)
    assert strong_res.overall_score > weak_res.overall_score
    # weights renormalize to sum 1.0
    assert sum(strong_res.weights_used.values()) == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_semantic_neutral_when_embedding_missing() -> None:
    """Missing embeddings yield a neutral 0.5 semantic score, not a bias."""
    prof = CandidateProfile(full_name="X", technical_skills=["python"])
    res = await compute_match(
        profile=prof,
        resume_embedding=None,
        job_embedding=None,
        required_skills=["python"],
        preferred_skills=[],
        min_experience_years=None,
        education_level=None,
        job_field_terms=None,
        weights=None,
        embedder=None,
    )
    assert res.semantic.score == 0.5
    assert res.semantic.cosine_similarity is None
