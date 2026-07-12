"""Ranker: scores every scored resume for a job and persists rankings."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CandidateJob, Job, Resume
from backend.database.repositories.candidate_job_repo import CandidateJobRepository
from backend.database.repositories.job_repo import JobRepository
from backend.database.repositories.resume_repo import ResumeRepository
from backend.embeddings.base import BaseEmbedder
from backend.matching.engine import compute_match
from backend.matching.schemas import MatchResult
from backend.resume.schemas import CandidateProfile

logger = structlog.get_logger(__name__)


def _job_field_terms(job: Job) -> list[str]:
    """Derive field-alignment terms for education from a job's fields."""
    terms: list[str] = []
    if job.department:
        terms.append(job.department)
    parsed = job.description_parsed or {}
    if isinstance(parsed, dict):
        field = parsed.get("field") or parsed.get("domain")
        if isinstance(field, str):
            terms.append(field)
    return terms


async def rank_job(
    *, session: AsyncSession, job_id: uuid.UUID, embedder: BaseEmbedder | None
) -> list[tuple[uuid.UUID, MatchResult]]:
    """Score all completed resumes for a job and persist their rankings.

    For each resume with a completed parse, computes an explainable MatchResult,
    upserts the candidate_jobs junction row with the composite and sub-scores,
    and stamps ``scored_at``. Returns results sorted by composite descending.

    Resumes without a completed parse are skipped (they have no profile yet).
    """
    job = await JobRepository(session).get(job_id)
    if job is None:
        raise ValueError(f"Job {job_id} not found")

    resumes = await ResumeRepository(session).get_by_job_id(job_id)
    cj_repo = CandidateJobRepository(session)
    field_terms = _job_field_terms(job)

    scored: list[tuple[uuid.UUID, MatchResult]] = []

    for resume in resumes:
        if resume.parsing_status != "completed" or resume.parsed_profile is None:
            continue
        if resume.candidate_id is None:
            continue

        profile = CandidateProfile.model_validate(resume.parsed_profile)
        result = await compute_match(
            profile=profile,
            resume_embedding=_as_list(resume.embedding),
            job_embedding=_as_list(job.embedding),
            required_skills=[str(s) for s in (job.required_skills or [])],
            preferred_skills=[str(s) for s in (job.preferred_skills or [])],
            min_experience_years=job.min_experience_years,
            education_level=job.education_level,
            job_field_terms=field_terms,
            weights=job.scoring_weights,
            embedder=embedder,
        )
        await _persist(cj_repo, session, resume, result)
        scored.append((resume.candidate_id, result))

    await session.commit()
    scored.sort(key=lambda pair: pair[1].overall_score, reverse=True)
    logger.info("job_ranked", job_id=str(job_id), candidates=len(scored))
    return scored


def _as_list(embedding) -> list[float] | None:  # type: ignore[no-untyped-def]
    """Coerce a stored embedding (list, pgvector, or None) to a float list."""
    if embedding is None:
        return None
    return [float(x) for x in embedding]


async def _persist(
    cj_repo: CandidateJobRepository,
    session: AsyncSession,
    resume: Resume,
    result: MatchResult,
) -> None:
    """Upsert the candidate_jobs row for a resume with its scores."""
    existing = await cj_repo.get_by_candidate_and_job(resume.candidate_id, resume.job_id)
    now = datetime.now(UTC)
    if existing is None:
        cj = CandidateJob(
            candidate_id=resume.candidate_id,
            job_id=resume.job_id,
            resume_id=resume.id,
            overall_score=result.overall_score,
            skill_score=result.skill.score,
            experience_score=result.experience.score,
            education_score=result.education.score,
            semantic_score=result.semantic.score,
            certification_score=result.certification.score,
            status="screened",
            scored_at=now,
        )
        session.add(cj)
    else:
        existing.resume_id = resume.id
        existing.overall_score = result.overall_score
        existing.skill_score = result.skill.score
        existing.experience_score = result.experience.score
        existing.education_score = result.education.score
        existing.semantic_score = result.semantic.score
        existing.certification_score = result.certification.score
        existing.scored_at = now
        if existing.status == "new":
            existing.status = "screened"
        session.add(existing)
    await session.flush()
