"""Report endpoints: SSE generation, saved retrieval, PDF download."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from backend.api.deps import CurrentUser, DbSession
from backend.core.exceptions import NotFoundException
from backend.services.report_service import ReportService

router = APIRouter(tags=["reports"])


class ReportOut(BaseModel):
    """A saved hiring report."""

    id: str
    summary: str
    strengths: list[Any]
    weaknesses: list[Any]
    recommendation: str | None
    risk_factors: list[Any]
    interview_plan: str | None
    model_used: str | None


@router.post("/jobs/{job_id}/candidates/{candidate_id}/report")
async def generate_report_endpoint(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    _user: CurrentUser,
    session: DbSession,
) -> StreamingResponse:
    """Generate a hiring report, streaming progress and the result as SSE."""
    return StreamingResponse(
        ReportService(session).stream_generate(job_id, candidate_id),
        media_type="text/event-stream",
    )


@router.get(
    "/jobs/{job_id}/candidates/{candidate_id}/report", response_model=ReportOut
)
async def get_report(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    _user: CurrentUser,
    session: DbSession,
) -> ReportOut:
    """Return the saved report for a candidate-job pairing."""
    report = await ReportService(session).get_saved(job_id, candidate_id)
    if report is None:
        raise NotFoundException("No report generated for this candidate")
    return ReportOut(
        id=str(report.id),
        summary=report.summary,
        strengths=report.strengths,
        weaknesses=report.weaknesses,
        recommendation=report.recommendation,
        risk_factors=report.risk_factors,
        interview_plan=report.interview_plan,
        model_used=report.model_used,
    )


@router.get("/jobs/{job_id}/candidates/{candidate_id}/report/pdf")
async def download_report_pdf(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    _user: CurrentUser,
    session: DbSession,
) -> Response:
    """Download the saved report as a PDF."""
    pdf_bytes = await ReportService(session).render_pdf(job_id, candidate_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=report_{candidate_id}.pdf"
        },
    )
