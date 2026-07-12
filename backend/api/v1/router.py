"""Assembles all v1 sub-routers into a single API router."""

from __future__ import annotations

from fastapi import APIRouter

from backend.api.v1 import (
    analytics,
    auth,
    candidates,
    health,
    interview_questions,
    jobs,
    reports,
    resumes,
    tasks,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(jobs.router)
api_router.include_router(resumes.router)
api_router.include_router(candidates.router)
api_router.include_router(interview_questions.router)
api_router.include_router(reports.router)
api_router.include_router(analytics.router)
api_router.include_router(tasks.router)
