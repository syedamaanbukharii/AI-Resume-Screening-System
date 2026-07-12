"""Candidate endpoints: ranked list, detail, status update, recruiter notes."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.api.deps import CurrentUser, DbSession
from backend.services.candidate_service import CandidateService

router = APIRouter(tags=["candidates"])


class RankedCandidate(BaseModel):
    """A candidate's scores and status on a job, for the ranked list."""

    candidate_id: str
    job_id: str
    resume_id: str
    overall_score: float | None
    skill_score: float | None
    experience_score: float | None
    education_score: float | None
    semantic_score: float | None
    certification_score: float | None
    status: str
    recruiter_notes: str | None


class CandidateProfileOut(BaseModel):
    """Full candidate profile across identity fields."""

    id: str
    email: str
    full_name: str
    phone: str | None
    linkedin_url: str | None
    github_url: str | None
    portfolio_url: str | None


class StatusUpdate(BaseModel):
    """Recruiter status-change payload."""

    status: str


class NotesUpdate(BaseModel):
    """Recruiter notes payload."""

    notes: str = Field(max_length=10000)


def _to_ranked(cj) -> RankedCandidate:  # type: ignore[no-untyped-def]
    """Map a candidate_jobs row to the ranked representation."""
    return RankedCandidate(
        candidate_id=str(cj.candidate_id),
        job_id=str(cj.job_id),
        resume_id=str(cj.resume_id),
        overall_score=cj.overall_score,
        skill_score=cj.skill_score,
        experience_score=cj.experience_score,
        education_score=cj.education_score,
        semantic_score=cj.semantic_score,
        certification_score=cj.certification_score,
        status=cj.status,
        recruiter_notes=cj.recruiter_notes,
    )


@router.get("/jobs/{job_id}/candidates", response_model=list[RankedCandidate])
async def list_ranked_candidates(
    job_id: uuid.UUID, _user: CurrentUser, session: DbSession
) -> list[RankedCandidate]:
    """List candidates for a job, ranked by composite score descending."""
    rows = await CandidateService(session).list_ranked_for_job(job_id)
    return [_to_ranked(r) for r in rows]


@router.get("/candidates/{candidate_id}", response_model=CandidateProfileOut)
async def get_candidate(
    candidate_id: uuid.UUID, _user: CurrentUser, session: DbSession
) -> CandidateProfileOut:
    """Return a candidate's identity profile across all jobs."""
    c = await CandidateService(session).get_candidate(candidate_id)
    return CandidateProfileOut(
        id=str(c.id),
        email=c.email,
        full_name=c.full_name,
        phone=c.phone,
        linkedin_url=c.linkedin_url,
        github_url=c.github_url,
        portfolio_url=c.portfolio_url,
    )


@router.get(
    "/jobs/{job_id}/candidates/{candidate_id}", response_model=RankedCandidate
)
async def get_candidate_for_job(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    _user: CurrentUser,
    session: DbSession,
) -> RankedCandidate:
    """Return a candidate's scores and status for a specific job."""
    cj = await CandidateService(session).get_for_job(candidate_id, job_id)
    return _to_ranked(cj)


@router.patch(
    "/jobs/{job_id}/candidates/{candidate_id}/status", response_model=RankedCandidate
)
async def update_candidate_status(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    payload: StatusUpdate,
    _user: CurrentUser,
    session: DbSession,
) -> RankedCandidate:
    """Update a candidate's status on a job (shortlist, reject, etc.)."""
    cj = await CandidateService(session).update_status(candidate_id, job_id, payload.status)
    return _to_ranked(cj)


@router.put(
    "/jobs/{job_id}/candidates/{candidate_id}/notes", response_model=RankedCandidate
)
async def update_candidate_notes(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    payload: NotesUpdate,
    _user: CurrentUser,
    session: DbSession,
) -> RankedCandidate:
    """Add or update recruiter notes on a candidate-job row."""
    cj = await CandidateService(session).update_notes(candidate_id, job_id, payload.notes)
    return _to_ranked(cj)
