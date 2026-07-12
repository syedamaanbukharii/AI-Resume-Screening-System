"""End-to-end resume processing pipeline.

Transaction discipline (the core correctness concern for batch scale):

1. A short transaction marks the resume/task as ``processing`` and commits,
   releasing the DB connection.
2. The slow work — text extraction, the LLM parse (15-45s), and embedding —
   runs holding NO database connection.
3. A second short transaction resolves/links the candidate, writes the parsed
   profile and embedding, and marks completion.

This keeps the connection pool free during long model calls, so a 50-200
resume batch does not exhaust it.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog

from backend.database.engine import async_session_factory
from backend.database.models import Candidate, Resume
from backend.database.repositories.candidate_repo import CandidateRepository
from backend.database.repositories.resume_repo import ResumeRepository
from backend.database.repositories.task_repo import TaskRepository
from backend.embeddings.factory import get_embedder
from backend.resume.extractor import extract_text
from backend.resume.normalizer import normalize_profile
from backend.resume.parser import parse_resume
from backend.resume.schemas import CandidateProfile
from backend.storage.local import get_storage
from backend.vectorstore.factory import get_vector_store

logger = structlog.get_logger(__name__)


async def _mark_processing(resume_id: uuid.UUID, task_id: uuid.UUID) -> tuple[str, str] | None:
    """Short txn: set statuses to processing; return (file_path, file_type)."""
    async with async_session_factory() as session:
        resume = await ResumeRepository(session).get(resume_id)
        if resume is None:
            logger.error("resume_not_found", resume_id=str(resume_id))
            return None
        resume.parsing_status = "processing"
        session.add(resume)
        task = await TaskRepository(session).get(task_id)
        if task is not None:
            task.status = "running"
            task.started_at = datetime.now(UTC)
            session.add(task)
        file_path, file_type = resume.file_path, resume.file_type
        await session.commit()
    return file_path, file_type


async def _resolve_candidate(
    session, profile: CandidateProfile
) -> uuid.UUID:
    """Find-or-create a candidate by email; return its id.

    Email is only known post-parse, so candidate resolution happens here. When
    no email is present, a synthetic unique candidate is created so the resume
    still links to exactly one candidate row.
    """
    repo = CandidateRepository(session)
    email = (profile.email or "").strip().lower()

    if email:
        existing = await repo.get_by_email(email)
        if existing is not None:
            return existing.id
        candidate = Candidate(
            email=email,
            full_name=profile.full_name,
            linkedin_url=profile.linkedin_url,
            github_url=profile.github_url,
            portfolio_url=profile.portfolio_url,
            phone=profile.phone,
        )
    else:
        candidate = Candidate(
            email=f"unknown+{uuid.uuid4().hex[:12]}@placeholder.local",
            full_name=profile.full_name,
            linkedin_url=profile.linkedin_url,
            github_url=profile.github_url,
            portfolio_url=profile.portfolio_url,
            phone=profile.phone,
        )
    session.add(candidate)
    await session.flush()
    return candidate.id


async def _write_success(
    resume_id: uuid.UUID,
    task_id: uuid.UUID,
    profile: CandidateProfile,
    embedding: list[float],
    model_name: str,
) -> None:
    """Short txn: link candidate, persist profile + embedding, mark complete."""
    async with async_session_factory() as session:
        resume = await ResumeRepository(session).get(resume_id)
        if resume is None:
            return
        candidate_id = await _resolve_candidate(session, profile)
        resume.candidate_id = candidate_id
        resume.parsed_profile = profile.model_dump()
        resume.parsing_status = "completed"
        resume.parsing_error = None
        session.add(resume)

        # Register with FAISS routing if that backend is active.
        store = get_vector_store(session)
        register = getattr(store, "register_resume_job", None)
        if callable(register):
            register(resume_id, resume.job_id)
        await store.upsert_resume(resume_id, embedding)

        task = await TaskRepository(session).get(task_id)
        if task is not None:
            task.status = "completed"
            task.completed_at = datetime.now(UTC)
            session.add(task)
        await session.commit()
        logger.info("resume_parsed", resume_id=str(resume_id), model=model_name)


async def _write_failure(resume_id: uuid.UUID, task_id: uuid.UUID, error: str) -> None:
    """Short txn: record a failed parse for manual review."""
    async with async_session_factory() as session:
        resume = await ResumeRepository(session).get(resume_id)
        if resume is not None:
            resume.parsing_status = "failed"
            resume.parsing_error = error[:2000]
            session.add(resume)
        task = await TaskRepository(session).get(task_id)
        if task is not None:
            task.status = "failed"
            task.error_message = error[:2000]
            task.completed_at = datetime.now(UTC)
            session.add(task)
        await session.commit()
    logger.warning("resume_parse_failed", resume_id=str(resume_id), error=error[:200])


async def run_resume_pipeline(resume_id: uuid.UUID, task_id: uuid.UUID) -> None:
    """Process one resume end to end. Intended to run as a background task.

    Never raises to the caller: all failures are recorded on the resume/task
    rows so the polling endpoint can report them.
    """
    marked = await _mark_processing(resume_id, task_id)
    if marked is None:
        await _write_failure(resume_id, task_id, "Resume row disappeared before processing")
        return
    file_path, file_type = marked

    try:
        # --- Slow work, holding NO DB connection ---
        raw_bytes = await get_storage().read(file_path)
        text = extract_text(raw_bytes, file_type)
        profile, model_name = await parse_resume(text)
        profile = normalize_profile(profile)
        embedding = await get_embedder().embed(profile.to_embedding_text())
    except Exception as exc:  # noqa: BLE001 - record any failure uniformly
        await _write_failure(resume_id, task_id, f"{type(exc).__name__}: {exc}")
        return

    # Persist raw text separately so it's available even if later steps changed.
    await _write_success(resume_id, task_id, profile, embedding, model_name)

    async with async_session_factory() as session:
        resume = await ResumeRepository(session).get(resume_id)
        if resume is not None and resume.raw_text is None:
            resume.raw_text = text
            session.add(resume)
            await session.commit()
