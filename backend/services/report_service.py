"""Report service: single-call generation, SSE streaming, PDF export."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.report_agent import GeneratedReport, generate_report
from backend.database.models import Report
from backend.services.scoring_context import build_scoring_context

logger = structlog.get_logger(__name__)


def _sse(event: str, data: dict) -> str:
    """Format a Server-Sent Event frame."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


class ReportService:
    """Coordinates report generation, persistence, and PDF export."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the session."""
        self.session = session

    async def stream_generate(
        self, job_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> AsyncGenerator[str, None]:
        """Generate a report, streaming coarse progress then the result.

        The report is a single structured call, so streaming here is honest
        about that: a 'start' frame, then the completed report (there are no
        intermediate reasoning steps to stream, unlike the interview graph).
        """
        try:
            ctx = await build_scoring_context(
                session=self.session, job_id=job_id, candidate_id=candidate_id
            )
        except Exception as exc:  # noqa: BLE001
            yield _sse("error", {"detail": str(exc)})
            return

        yield _sse("start", {"candidate": ctx.profile.full_name, "job": ctx.job.title})

        try:
            report = await generate_report(
                candidate_name=ctx.profile.full_name,
                job_title=ctx.job.title,
                overall_score=ctx.match.overall_score,
                sub_scores=ctx.match.sub_scores(),
                matched_skills=ctx.matched_skills,
                missing_required=ctx.match.skill.missing_required,
                profile_summary=ctx.profile.summary or "",
                rationales=ctx.rationales,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("report_stream_failed", error=str(exc))
            yield _sse("error", {"detail": str(exc)})
            return

        await self._persist(ctx.candidate_job.id, report)
        yield _sse("complete", report.model_dump())

    async def _persist(self, candidate_job_id: uuid.UUID, report: GeneratedReport) -> None:
        """Replace any existing report for a pairing and persist the new one."""
        from sqlalchemy import delete

        await self.session.execute(
            delete(Report).where(Report.candidate_job_id == candidate_job_id)
        )
        self.session.add(
            Report(
                candidate_job_id=candidate_job_id,
                summary=report.summary,
                strengths=report.strengths,
                weaknesses=report.weaknesses,
                recommendation=report.recommendation,
                risk_factors=report.risk_factors,
                interview_plan=report.interview_plan,
                model_used=report.model_used,
            )
        )
        await self.session.commit()

    async def get_saved(
        self, job_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> Report | None:
        """Return the saved report for a candidate-job pairing, if any."""
        ctx = await build_scoring_context(
            session=self.session, job_id=job_id, candidate_id=candidate_id
        )
        result = await self.session.execute(
            select(Report).where(Report.candidate_job_id == ctx.candidate_job.id)
        )
        return result.scalar_one_or_none()

    async def render_pdf(self, job_id: uuid.UUID, candidate_id: uuid.UUID) -> bytes:
        """Render the saved report to PDF bytes using reportlab."""
        ctx = await build_scoring_context(
            session=self.session, job_id=job_id, candidate_id=candidate_id
        )
        report = await self.get_saved(job_id, candidate_id)
        if report is None:
            from backend.core.exceptions import NotFoundException

            raise NotFoundException("No report generated for this candidate")
        return _build_pdf(
            candidate_name=ctx.profile.full_name,
            job_title=ctx.job.title,
            overall_score=ctx.match.overall_score,
            report=report,
        )


def _build_pdf(
    *, candidate_name: str, job_title: str, overall_score: float, report: Report
) -> bytes:
    """Build a report PDF and return its bytes."""
    import io

    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Candidate Report: {candidate_name}", styles["Title"]))
    story.append(Paragraph(f"Role: {job_title}", styles["Normal"]))
    story.append(Paragraph(f"Overall match: {overall_score:.1%}", styles["Normal"]))
    story.append(
        Paragraph(f"Recommendation: {report.recommendation or 'neutral'}", styles["Heading2"])
    )
    story.append(Spacer(1, 12))

    story.append(Paragraph("Summary", styles["Heading2"]))
    story.append(Paragraph(report.summary, styles["Normal"]))
    story.append(Spacer(1, 12))

    def _section(title: str, items: list) -> None:
        story.append(Paragraph(title, styles["Heading2"]))
        for item in items or ["None noted."]:
            story.append(Paragraph(f"• {item}", styles["Normal"]))
        story.append(Spacer(1, 12))

    _section("Strengths", report.strengths)
    _section("Weaknesses", report.weaknesses)
    _section("Risk factors", report.risk_factors)

    if report.interview_plan:
        story.append(Paragraph("Interview plan", styles["Heading2"]))
        story.append(Paragraph(report.interview_plan, styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()
