"""Interview-question endpoints: SSE generation stream and saved retrieval."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.api.deps import CurrentUser, DbSession
from backend.services.interview_service import InterviewService

router = APIRouter(tags=["interview"])


class QuestionOut(BaseModel):
    """A saved interview question."""

    id: str
    category: str
    difficulty: str
    question: str
    expected_answer: str | None
    evaluation_criteria: str | None


@router.post("/jobs/{job_id}/candidates/{candidate_id}/questions")
async def generate_questions(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    _user: CurrentUser,
    session: DbSession,
) -> StreamingResponse:
    """Generate interview questions, streaming graph progress as SSE."""
    service = InterviewService(session)
    return StreamingResponse(
        service.stream_generate(job_id, candidate_id),
        media_type="text/event-stream",
    )


@router.get(
    "/jobs/{job_id}/candidates/{candidate_id}/questions",
    response_model=list[QuestionOut],
)
async def get_questions(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    _user: CurrentUser,
    session: DbSession,
) -> list[QuestionOut]:
    """Return saved interview questions for a candidate-job pairing."""
    rows = await InterviewService(session).get_saved(job_id, candidate_id)
    return [
        QuestionOut(
            id=str(r.id),
            category=r.category,
            difficulty=r.difficulty,
            question=r.question,
            expected_answer=r.expected_answer,
            evaluation_criteria=r.evaluation_criteria,
        )
        for r in rows
    ]
