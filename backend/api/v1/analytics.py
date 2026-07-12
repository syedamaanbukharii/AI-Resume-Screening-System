"""Analytics endpoints: dashboard and per-job aggregates."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.api.deps import CurrentUser, DbSession
from backend.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


class DashboardStats(BaseModel):
    """Top-level dashboard metrics."""

    total_jobs: int
    active_jobs: int
    total_candidates: int
    avg_score: float | None
    funnel: dict[str, int]


class JobAnalytics(BaseModel):
    """Per-job score distribution and status breakdown."""

    job_id: str
    score_distribution: list[dict[str, Any]]
    status_breakdown: dict[str, int]


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(_user: CurrentUser, session: DbSession) -> DashboardStats:
    """Return dashboard-wide counts, average score, and the status funnel."""
    data = await AnalyticsService(session).dashboard()
    return DashboardStats(**data)


@router.get("/jobs/{job_id}", response_model=JobAnalytics)
async def get_job_analytics(
    job_id: uuid.UUID, _user: CurrentUser, session: DbSession
) -> JobAnalytics:
    """Return per-job score distribution and status breakdown."""
    data = await AnalyticsService(session).job_analytics(job_id)
    return JobAnalytics(**data)
