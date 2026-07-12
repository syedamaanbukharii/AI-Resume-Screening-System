"""Job endpoints: CRUD and status lifecycle."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Query, status
from pydantic import BaseModel, Field

from backend.api.deps import CurrentUser, DbSession
from backend.services.job_service import JobService
from backend.services.ranking_service import RankingService

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobCreate(BaseModel):
    """Payload for creating a job posting."""

    title: str = Field(min_length=1, max_length=300)
    description_raw: str = Field(min_length=1)
    department: str | None = Field(default=None, max_length=100)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_experience_years: int | None = None
    education_level: str | None = Field(default=None, max_length=50)


class JobUpdate(BaseModel):
    """Partial-update payload for a job."""

    title: str | None = Field(default=None, max_length=300)
    description_raw: str | None = None
    department: str | None = Field(default=None, max_length=100)
    required_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    min_experience_years: int | None = None
    education_level: str | None = Field(default=None, max_length=50)


class JobStatusUpdate(BaseModel):
    """Status-change payload."""

    status: str


class JobOut(BaseModel):
    """Public job representation."""

    id: str
    title: str
    department: str | None
    description_raw: str
    required_skills: list[Any]
    preferred_skills: list[Any]
    min_experience_years: int | None
    education_level: str | None
    status: str
    created_by: str | None

    model_config = {"from_attributes": True}


def _to_out(job) -> JobOut:  # type: ignore[no-untyped-def]
    """Map an ORM job to its public representation."""
    return JobOut(
        id=str(job.id),
        title=job.title,
        department=job.department,
        description_raw=job.description_raw,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        min_experience_years=job.min_experience_years,
        education_level=job.education_level,
        status=job.status,
        created_by=str(job.created_by) if job.created_by else None,
    )


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    user: CurrentUser,
    session: DbSession,
    background: BackgroundTasks,
) -> JobOut:
    """Create a new job posting and embed its description in the background."""
    job = await JobService(session).create_job(
        created_by=user.id, **payload.model_dump()
    )
    await session.commit()

    async def _embed(job_id) -> None:  # type: ignore[no-untyped-def]
        """Embed the JD on a fresh session so it holds no request connection."""
        from backend.database.engine import async_session_factory

        async with async_session_factory() as s:
            await RankingService(s).embed_job_description(job_id)

    background.add_task(_embed, job.id)
    return _to_out(job)


class RankResult(BaseModel):
    """Summary returned after triggering a ranking run."""

    job_id: str
    ranked_count: int
    top_candidate_id: str | None
    top_score: float | None


@router.post("/{job_id}/rank", response_model=RankResult)
async def rank_candidates(
    job_id: uuid.UUID, _user: CurrentUser, session: DbSession
) -> RankResult:
    """Score and rank all completed candidates for a job."""
    results = await RankingService(session).rank(job_id)
    top = results[0] if results else None
    return RankResult(
        job_id=str(job_id),
        ranked_count=len(results),
        top_candidate_id=str(top[0]) if top else None,
        top_score=top[1].overall_score if top else None,
    )


@router.get("", response_model=list[JobOut])
async def list_jobs(
    _user: CurrentUser,
    session: DbSession,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = 50,
    offset: int = 0,
) -> list[JobOut]:
    """List jobs with optional status filter and pagination."""
    jobs = await JobService(session).list_jobs(status=status_filter, limit=limit, offset=offset)
    return [_to_out(j) for j in jobs]


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: uuid.UUID, _user: CurrentUser, session: DbSession) -> JobOut:
    """Return a single job by id."""
    job = await JobService(session).get_job(job_id)
    return _to_out(job)


@router.put("/{job_id}", response_model=JobOut)
async def update_job(
    job_id: uuid.UUID, payload: JobUpdate, _user: CurrentUser, session: DbSession
) -> JobOut:
    """Apply partial updates to a job."""
    job = await JobService(session).update_job(job_id, **payload.model_dump())
    await session.commit()
    return _to_out(job)


@router.patch("/{job_id}/status", response_model=JobOut)
async def change_status(
    job_id: uuid.UUID, payload: JobStatusUpdate, _user: CurrentUser, session: DbSession
) -> JobOut:
    """Transition a job to a new lifecycle status."""
    job = await JobService(session).change_status(job_id, payload.status)
    await session.commit()
    return _to_out(job)


@router.delete("/{job_id}", response_model=JobOut)
async def delete_job(job_id: uuid.UUID, _user: CurrentUser, session: DbSession) -> JobOut:
    """Soft-delete a job by archiving it."""
    job = await JobService(session).delete_job(job_id)
    await session.commit()
    return _to_out(job)
