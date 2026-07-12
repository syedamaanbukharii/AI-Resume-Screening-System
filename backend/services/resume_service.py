"""Resume service: upload orchestration and task enqueueing."""

from __future__ import annotations

import uuid

import structlog
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.exceptions import NotFoundException, ValidationException
from backend.database.models import JobProcessingTask, Resume
from backend.database.repositories.job_repo import JobRepository
from backend.database.repositories.resume_repo import ResumeRepository
from backend.resume.pipeline import run_resume_pipeline
from backend.storage.local import get_storage

logger = structlog.get_logger(__name__)


class UploadedFile:
    """A minimal, framework-agnostic view of an uploaded file."""

    def __init__(self, filename: str, content: bytes) -> None:
        """Capture filename and raw content."""
        self.filename = filename
        self.content = content


class ResumeService:
    """Coordinates resume intake: validation, storage, and enqueueing."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind repositories to the request session."""
        self.session = session
        self.resumes = ResumeRepository(session)
        self.jobs = JobRepository(session)
        self.storage = get_storage()

    def _validate(self, filename: str, content: bytes) -> str:
        """Validate file type and size; return the lowercase extension."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in settings.ALLOWED_FILE_TYPES:
            raise ValidationException(
                f"Unsupported file type '{ext}'. Allowed: {settings.ALLOWED_FILE_TYPES}"
            )
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) == 0:
            raise ValidationException("Empty file")
        if len(content) > max_bytes:
            raise ValidationException(
                f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit"
            )
        return ext

    async def upload_resumes(
        self,
        *,
        job_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        files: list[UploadedFile],
        background: BackgroundTasks,
    ) -> list[dict[str, str]]:
        """Store each file, create resume + task rows, and enqueue parsing.

        Returns a list of {resume_id, task_id, filename, status} descriptors.
        The candidate_id is intentionally left null until the background parse
        resolves the candidate from the extracted email.
        """
        job = await self.jobs.get(job_id)
        if job is None:
            raise NotFoundException("Job not found")

        results: list[dict[str, str]] = []
        pending: list[tuple[uuid.UUID, uuid.UUID]] = []

        for file in files:
            ext = self._validate(file.filename, file.content)
            resume_id = uuid.uuid4()
            key = f"{job_id}/{resume_id}.{ext}"
            path = await self.storage.save(key=key, data=file.content)

            resume = Resume(
                id=resume_id,
                candidate_id=None,
                job_id=job_id,
                filename=file.filename,
                file_path=path,
                file_type=ext,
                file_size_bytes=len(file.content),
                parsing_status="pending",
                uploaded_by=uploaded_by,
            )
            self.session.add(resume)

            task = JobProcessingTask(
                task_type="resume_parse",
                reference_id=resume_id,
                status="pending",
            )
            self.session.add(task)
            await self.session.flush()

            pending.append((resume_id, task.id))
            results.append(
                {
                    "resume_id": str(resume_id),
                    "task_id": str(task.id),
                    "filename": file.filename,
                    "status": "pending",
                }
            )

        await self.session.commit()

        # Enqueue only after commit so the background task sees persisted rows.
        for resume_id, task_id in pending:
            background.add_task(run_resume_pipeline, resume_id, task_id)

        return results

    async def get_resume(self, resume_id: uuid.UUID) -> Resume:
        """Return a resume by id or raise NotFound."""
        resume = await self.resumes.get(resume_id)
        if resume is None:
            raise NotFoundException("Resume not found")
        return resume

    async def list_for_job(self, job_id: uuid.UUID) -> list[Resume]:
        """Return all resumes uploaded for a job."""
        return await self.resumes.get_by_job_id(job_id)

    async def delete_resume(self, resume_id: uuid.UUID) -> None:
        """Delete a resume row and its stored file."""
        resume = await self.get_resume(resume_id)
        await self.storage.delete(resume.file_path)
        await self.resumes.delete(resume_id)
        await self.session.commit()
