"""Interview service: runs the LangGraph agent, streams progress, persists."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.interview_agent import get_interview_graph
from backend.agents.state import InterviewState
from backend.database.models import InterviewQuestion
from backend.services.scoring_context import build_scoring_context

logger = structlog.get_logger(__name__)

_DEFAULT_CATEGORIES = ["technical", "behavioral", "scenario", "coding"]


def _sse(event: str, data: dict) -> str:
    """Format a Server-Sent Event frame."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


class InterviewService:
    """Coordinates interview generation via the graph and persistence."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the session."""
        self.session = session

    async def _initial_state(
        self, job_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> tuple[InterviewState, uuid.UUID]:
        """Build the graph's initial state from scoring context."""
        ctx = await build_scoring_context(
            session=self.session, job_id=job_id, candidate_id=candidate_id
        )
        state: InterviewState = {
            "candidate_name": ctx.profile.full_name,
            "profile_summary": ctx.profile.summary or "",
            "job_title": ctx.job.title,
            "required_skills": [str(s) for s in (ctx.job.required_skills or [])],
            "missing_required": ctx.match.skill.missing_required,
            "matched_skills": ctx.matched_skills,
            "target_categories": _DEFAULT_CATEGORIES,
            "current_category": _DEFAULT_CATEGORIES[0],
            "questions": [],
            "covered_categories": [],
            "followup_rounds": 0,
            "max_followup_rounds": 1,
            "errors": [],
        }
        return state, ctx.candidate_job.id

    async def stream_generate(
        self, job_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> AsyncGenerator[str, None]:
        """Run the graph, yielding SSE frames as each node completes.

        Streaming reflects the graph's real progress: one frame per node
        transition (category generated, follow-ups generated), then a final
        persisted-count frame. Consumes the graph's async event stream.
        """
        try:
            state, candidate_job_id = await self._initial_state(job_id, candidate_id)
        except Exception as exc:  # noqa: BLE001
            yield _sse("error", {"detail": str(exc)})
            return

        graph = get_interview_graph()
        collected: list = []
        model_used: str | None = None
        yield _sse("start", {"categories": state["target_categories"]})

        try:
            async for step in graph.astream(state):
                for node_name, node_output in step.items():
                    node_output = node_output or {}
                    new_qs = (
                        node_output.get("questions", [])
                        if isinstance(node_output, dict)
                        else []
                    )
                    collected.extend(new_qs)
                    if isinstance(node_output, dict) and node_output.get("model_used"):
                        model_used = node_output["model_used"]
                    yield _sse(
                        "progress",
                        {"node": node_name, "questions_generated": len(new_qs)},
                    )
        except Exception as exc:  # noqa: BLE001
            logger.error("interview_stream_failed", error=str(exc))
            yield _sse("error", {"detail": str(exc)})
            return

        saved = await self._persist(candidate_job_id, collected)
        yield _sse("complete", {"saved": saved, "model_used": model_used})

    async def _persist(self, candidate_job_id: uuid.UUID, questions: list) -> int:
        """Replace existing questions for a pairing and persist the new set."""
        from sqlalchemy import delete

        await self.session.execute(
            delete(InterviewQuestion).where(
                InterviewQuestion.candidate_job_id == candidate_job_id
            )
        )
        for q in questions:
            self.session.add(
                InterviewQuestion(
                    candidate_job_id=candidate_job_id,
                    category=q["category"],
                    difficulty=q.get("difficulty", "medium"),
                    question=q["question"],
                    expected_answer=q.get("expected_answer"),
                    evaluation_criteria=q.get("evaluation_criteria"),
                )
            )
        await self.session.commit()
        return len(questions)

    async def get_saved(
        self, job_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> list[InterviewQuestion]:
        """Return saved questions for a candidate-job pairing."""
        from sqlalchemy import select

        ctx = await build_scoring_context(
            session=self.session, job_id=job_id, candidate_id=candidate_id
        )
        result = await self.session.execute(
            select(InterviewQuestion).where(
                InterviewQuestion.candidate_job_id == ctx.candidate_job.id
            )
        )
        return list(result.scalars().all())
