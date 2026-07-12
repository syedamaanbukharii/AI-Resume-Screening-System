"""Helper to rebuild scoring evidence for agent inputs.

The ranker persists sub-scores (numbers) but not the full evidence trail. The
interview and report agents need the evidence (matched/missing skills,
rationales), so this recomputes the deterministic MatchResult on demand — it is
cheap, pure, and avoids storing a large evidence blob per candidate.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundException, ValidationException
from backend.database.models import CandidateJob, Job, Resume
from backend.database.repositories.candidate_job_repo import CandidateJobRepository
from backend.database.repositories.job_repo import JobRepository
from backend.database.repositories.resume_repo import ResumeRepository
from backend.embeddings.base import BaseEmbedder, EmbeddingError
from backend.embeddings.factory import get_embedder
from backend.matching.engine import compute_match
from backend.matching.ranker import _job_field_terms
from backend.matching.schemas import MatchResult
from backend.resume.schemas import CandidateProfile


class ScoringContext:
    """Bundled inputs the agents need: profile, match result, and job."""

    def __init__(
        self, *, profile: CandidateProfile, match: MatchResult, job: Job, candidate_job: CandidateJob
    ) -> None:
        """Store the reconstructed scoring context."""
        self.profile = profile
        self.match = match
        self.job = job
        self.candidate_job = candidate_job

    @property
    def matched_skills(self) -> list[str]:
        """Return skills matched exactly or semantically."""
        return [e.skill for e in self.match.skill.matched_exact] + [
            e.skill for e in self.match.skill.matched_semantic
        ]

    @property
    def rationales(self) -> dict[str, str]:
        """Return per-factor rationales keyed by factor name."""
        return {
            "skill": self.match.skill.rationale,
            "experience": self.match.experience.rationale,
            "education": self.match.education.rationale,
            "semantic": self.match.semantic.rationale,
            "certification": self.match.certification.rationale,
        }


async def build_scoring_context(
    *, session: AsyncSession, job_id: uuid.UUID, candidate_id: uuid.UUID
) -> ScoringContext:
    """Reconstruct the deterministic scoring context for a candidate-job pair.

    Raises:
        NotFoundException: If the pairing, job, or a completed resume is missing.
        ValidationException: If the resume has no parsed profile.
    """
    cj = await CandidateJobRepository(session).get_by_candidate_and_job(candidate_id, job_id)
    if cj is None:
        raise NotFoundException("Candidate is not associated with this job")

    job = await JobRepository(session).get(job_id)
    if job is None:
        raise NotFoundException("Job not found")

    resume = await ResumeRepository(session).get(cj.resume_id)
    if resume is None or resume.parsed_profile is None:
        raise ValidationException("No parsed resume available for this candidate")

    profile = CandidateProfile.model_validate(resume.parsed_profile)

    try:
        embedder: BaseEmbedder | None = get_embedder()
    except EmbeddingError:
        embedder = None

    match = await compute_match(
        profile=profile,
        resume_embedding=[float(x) for x in resume.embedding] if resume.embedding else None,
        job_embedding=[float(x) for x in job.embedding] if job.embedding else None,
        required_skills=[str(s) for s in (job.required_skills or [])],
        preferred_skills=[str(s) for s in (job.preferred_skills or [])],
        min_experience_years=job.min_experience_years,
        education_level=job.education_level,
        job_field_terms=_job_field_terms(job),
        weights=job.scoring_weights,
        embedder=embedder,
    )
    return ScoringContext(profile=profile, match=match, job=job, candidate_job=cj)
