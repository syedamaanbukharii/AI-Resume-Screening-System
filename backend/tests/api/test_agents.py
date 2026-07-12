"""Hermetic tests for the interview graph and report agent (mocked LLM)."""

from __future__ import annotations

import json

import pytest


class _FakeRouter:
    """A router stub returning category, follow-up, or report JSON."""

    async def complete_json(self, system: str, user: str) -> tuple[str, str]:
        """Return canned JSON keyed by which agent prompt is calling."""
        low = system.lower()
        if "follow-up" in low or "follow" in low and "probe" in low:
            return (
                json.dumps(
                    {
                        "questions": [
                            {
                                "difficulty": "hard",
                                "question": "Probe kubernetes networking.",
                                "expected_answer": "CNI, services, ingress.",
                                "evaluation_criteria": "depth",
                                "probes_gap": "kubernetes",
                            }
                        ]
                    }
                ),
                "fake",
            )
        if "hiring report" in low:
            return (
                json.dumps(
                    {
                        "summary": "Strong fit with a kubernetes gap.",
                        "strengths": ["python", "pytorch"],
                        "weaknesses": ["kubernetes unproven"],
                        "recommendation": "recommend",
                        "risk_factors": ["unverified kubernetes"],
                        "interview_plan": "Focus on kubernetes depth.",
                    }
                ),
                "fake",
            )
        return (
            json.dumps(
                {
                    "questions": [
                        {"difficulty": "easy", "question": "qe", "expected_answer": "a",
                         "evaluation_criteria": "c", "probes_gap": None},
                        {"difficulty": "medium", "question": "qm", "expected_answer": "a",
                         "evaluation_criteria": "c", "probes_gap": None},
                        {"difficulty": "hard", "question": "qh", "expected_answer": "a",
                         "evaluation_criteria": "c", "probes_gap": "python"},
                    ]
                }
            ),
            "fake",
        )


@pytest.mark.asyncio
async def test_interview_graph_conditional_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """The graph covers every category then loops once into follow-ups."""
    import backend.agents.interview_agent as ia

    monkeypatch.setattr(ia, "get_llm_router", lambda: _FakeRouter())
    graph = ia.build_interview_graph()

    state = {
        "candidate_name": "Jane",
        "profile_summary": "ML engineer",
        "job_title": "ML Engineer",
        "required_skills": ["python", "kubernetes"],
        "missing_required": ["kubernetes"],
        "matched_skills": ["python", "pytorch"],
        "target_categories": ["technical", "behavioral"],
        "current_category": "technical",
        "questions": [],
        "covered_categories": [],
        "followup_rounds": 0,
        "max_followup_rounds": 1,
        "errors": [],
    }

    collected: list = []
    rounds = 0
    async for step in graph.astream(state):
        for _node, out in step.items():
            out = out or {}
            collected.extend(out.get("questions", []) if isinstance(out, dict) else [])
            if isinstance(out, dict) and "followup_rounds" in out:
                rounds = out["followup_rounds"]

    categories = {q["category"] for q in collected}
    # 2 categories x 3 + 1 follow-up
    assert len(collected) == 7
    assert "followup" in categories
    assert rounds == 1  # terminates after max_followup_rounds


@pytest.mark.asyncio
async def test_interview_no_followup_when_no_gaps(monkeypatch: pytest.MonkeyPatch) -> None:
    """With no unmet required skills, the graph does not loop into follow-ups."""
    import backend.agents.interview_agent as ia

    monkeypatch.setattr(ia, "get_llm_router", lambda: _FakeRouter())
    graph = ia.build_interview_graph()
    state = {
        "candidate_name": "Jane",
        "profile_summary": "",
        "job_title": "ML Engineer",
        "required_skills": ["python"],
        "missing_required": [],  # no gaps
        "matched_skills": ["python"],
        "target_categories": ["technical"],
        "current_category": "technical",
        "questions": [],
        "covered_categories": [],
        "followup_rounds": 0,
        "max_followup_rounds": 1,
        "errors": [],
    }
    collected: list = []
    async for step in graph.astream(state):
        for _node, out in step.items():
            out = out or {}
            collected.extend(out.get("questions", []) if isinstance(out, dict) else [])
    assert all(q["category"] != "followup" for q in collected)


@pytest.mark.asyncio
async def test_report_agent_single_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """The report agent returns a validated, grounded report in one call."""
    import backend.agents.report_agent as ra

    monkeypatch.setattr(ra, "get_llm_router", lambda: _FakeRouter())
    report = await ra.generate_report(
        candidate_name="Jane",
        job_title="ML Engineer",
        overall_score=0.82,
        sub_scores={"skill": 0.5, "experience": 1.0, "education": 1.0,
                    "semantic": 0.5, "certification": 0.0},
        matched_skills=["python", "pytorch"],
        missing_required=["kubernetes"],
        profile_summary="ML engineer",
        rationales={"skill": "1 required unmet"},
    )
    assert report.recommendation == "recommend"
    assert "python" in report.strengths
    assert report.model_used == "fake"


@pytest.mark.asyncio
async def test_report_agent_invalid_recommendation_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An out-of-enum recommendation is coerced to neutral, not rejected."""
    import backend.agents.report_agent as ra

    class BadRec:
        async def complete_json(self, s: str, u: str) -> tuple[str, str]:
            return json.dumps({"summary": "x", "recommendation": "hire_immediately"}), "m"

    monkeypatch.setattr(ra, "get_llm_router", lambda: BadRec())
    report = await ra.generate_report(
        candidate_name="X", job_title="Y", overall_score=0.5,
        sub_scores={}, matched_skills=[], missing_required=[],
        profile_summary="", rationales={},
    )
    assert report.recommendation == "neutral"
