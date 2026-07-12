"""Report agent: a single structured LLM call — deliberately NOT a graph.

The report has all inputs up front (profile, scoring evidence, JD) and produces
one structured object. There is no branching, no cycle, no accumulating state —
so it is a plain structured-output call, exactly like the resume parser. Using
LangGraph here would add state-machine ceremony with no reasoning benefit, the
same anti-pattern the architecture review already removed from the spec.
"""

from __future__ import annotations

import json

import structlog
from pydantic import BaseModel, Field, ValidationError

from backend.llms.router import get_llm_router
from backend.prompts.report.generate import SYSTEM_PROMPT, build_user_prompt

logger = structlog.get_logger(__name__)

_VALID_RECOMMENDATIONS = {
    "strongly_recommend",
    "recommend",
    "neutral",
    "not_recommend",
}


class GeneratedReport(BaseModel):
    """Validated structure of a generated hiring report."""

    summary: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendation: str = "neutral"
    risk_factors: list[str] = Field(default_factory=list)
    interview_plan: str | None = None
    model_used: str | None = None


class ReportError(Exception):
    """Raised when report generation fails or returns invalid output."""


def _strip_fences(raw: str) -> str:
    """Remove markdown fences from an LLM JSON payload."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else text
        if text.endswith("```"):
            text = text[: text.rfind("```")]
    return text.strip()


async def generate_report(
    *,
    candidate_name: str,
    job_title: str,
    overall_score: float,
    sub_scores: dict[str, float],
    matched_skills: list[str],
    missing_required: list[str],
    profile_summary: str,
    rationales: dict[str, str],
) -> GeneratedReport:
    """Generate a validated hiring report in a single structured call.

    Raises:
        ReportError: On LLM failure or invalid/unshaped output.
    """
    prompt = build_user_prompt(
        candidate_name=candidate_name,
        job_title=job_title,
        overall_score=overall_score,
        sub_scores=sub_scores,
        matched_skills=matched_skills,
        missing_required=missing_required,
        profile_summary=profile_summary,
        rationales=rationales,
    )
    try:
        raw, model = await get_llm_router().complete_json(SYSTEM_PROMPT, prompt)
    except Exception as exc:  # noqa: BLE001
        raise ReportError(f"Report LLM call failed: {exc}") from exc

    try:
        payload = json.loads(_strip_fences(raw))
    except json.JSONDecodeError as exc:
        raise ReportError(f"Report returned invalid JSON: {exc}") from exc

    if payload.get("recommendation") not in _VALID_RECOMMENDATIONS:
        payload["recommendation"] = "neutral"

    try:
        report = GeneratedReport.model_validate(payload)
    except ValidationError as exc:
        raise ReportError(f"Report failed schema validation: {exc}") from exc
    report.model_used = model
    return report
