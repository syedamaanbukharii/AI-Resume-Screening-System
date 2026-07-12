"""Analytics service: dashboard and per-job aggregates."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundException
from backend.database.models import CandidateJob, Job


class AnalyticsService:
    """Computes dashboard and per-job analytics from persisted rankings."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the session."""
        self.session = session

    async def dashboard(self) -> dict:
        """Return top-level counts, average score, and the status funnel."""
        total_jobs = int(
            (await self.session.execute(select(func.count()).select_from(Job))).scalar_one()
        )
        active_jobs = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(Job).where(Job.status == "active")
                )
            ).scalar_one()
        )
        total_candidates = int(
            (
                await self.session.execute(
                    select(func.count(func.distinct(CandidateJob.candidate_id)))
                )
            ).scalar_one()
        )
        avg_score = (
            await self.session.execute(select(func.avg(CandidateJob.overall_score)))
        ).scalar_one()

        funnel_rows = await self.session.execute(
            select(CandidateJob.status, func.count()).group_by(CandidateJob.status)
        )
        funnel = {status: int(count) for status, count in funnel_rows.all()}

        return {
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "total_candidates": total_candidates,
            "avg_score": float(avg_score) if avg_score is not None else None,
            "funnel": funnel,
        }

    async def job_analytics(self, job_id: uuid.UUID) -> dict:
        """Return score-band distribution and status breakdown for one job."""
        job = await self.session.get(Job, job_id)
        if job is None:
            raise NotFoundException("Job not found")

        rows = await self.session.execute(
            select(CandidateJob.overall_score, CandidateJob.status).where(
                CandidateJob.job_id == job_id
            )
        )
        bands = {"high": 0, "mid": 0, "low": 0, "unscored": 0}
        status_breakdown: dict[str, int] = {}
        for score, status in rows.all():
            if score is None:
                bands["unscored"] += 1
            elif score >= 0.7:
                bands["high"] += 1
            elif score >= 0.45:
                bands["mid"] += 1
            else:
                bands["low"] += 1
            status_breakdown[status] = status_breakdown.get(status, 0) + 1

        return {
            "job_id": str(job_id),
            "score_distribution": [{"band": b, "count": c} for b, c in bands.items()],
            "status_breakdown": status_breakdown,
        }
