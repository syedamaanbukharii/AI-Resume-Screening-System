"""Resume endpoints: multipart upload (batch), list, detail, delete."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, UploadFile, status
from pydantic import BaseModel

from backend.api.deps import CurrentUser, DbSession
from backend.services.resume_service import ResumeService, UploadedFile

router = APIRouter(tags=["resumes"])


class UploadResult(BaseModel):
    """Descriptor for one enqueued resume."""

    resume_id: str
    task_id: str
    filename: str
    status: str


class ResumeDetail(BaseModel):
    """Resume detail including parsing status and parsed profile."""

    id: str
    job_id: str
    candidate_id: str | None
    filename: str
    file_type: str
    file_size_bytes: int
    parsing_status: str
    parsing_error: str | None
    parsed_profile: dict[str, Any] | None

    model_config = {"from_attributes": True}


def _to_detail(resume) -> ResumeDetail:  # type: ignore[no-untyped-def]
    """Map an ORM resume to its detail representation."""
    return ResumeDetail(
        id=str(resume.id),
        job_id=str(resume.job_id),
        candidate_id=str(resume.candidate_id) if resume.candidate_id else None,
        filename=resume.filename,
        file_type=resume.file_type,
        file_size_bytes=resume.file_size_bytes,
        parsing_status=resume.parsing_status,
        parsing_error=resume.parsing_error,
        parsed_profile=resume.parsed_profile,
    )


@router.post(
    "/jobs/{job_id}/resumes",
    response_model=list[UploadResult],
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_resumes(
    job_id: uuid.UUID,
    user: CurrentUser,
    session: DbSession,
    background: BackgroundTasks,
    files: list[UploadFile] = File(...),
) -> list[UploadResult]:
    """Upload one or more resumes for a job and enqueue background parsing."""
    payload = [UploadedFile(f.filename or "resume", await f.read()) for f in files]
    results = await ResumeService(session).upload_resumes(
        job_id=job_id,
        uploaded_by=user.id,
        files=payload,
        background=background,
    )
    return [UploadResult(**r) for r in results]


@router.get("/jobs/{job_id}/resumes", response_model=list[ResumeDetail])
async def list_resumes(
    job_id: uuid.UUID, _user: CurrentUser, session: DbSession
) -> list[ResumeDetail]:
    """List all resumes uploaded for a job."""
    resumes = await ResumeService(session).list_for_job(job_id)
    return [_to_detail(r) for r in resumes]


@router.get("/resumes/{resume_id}", response_model=ResumeDetail)
async def get_resume(
    resume_id: uuid.UUID, _user: CurrentUser, session: DbSession
) -> ResumeDetail:
    """Return a single resume's detail and parsing status."""
    resume = await ResumeService(session).get_resume(resume_id)
    return _to_detail(resume)


@router.delete("/resumes/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: uuid.UUID, _user: CurrentUser, session: DbSession
):
    """Delete a resume record and its stored file."""
    from fastapi import Response

    await ResumeService(session).delete_resume(resume_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
