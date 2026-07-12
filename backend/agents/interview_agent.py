"""Interview agent: a LangGraph state machine with conditional follow-up loops.

Why a graph here (and not for the report): the interview generation genuinely
needs stateful, conditional control flow —

  generate_category  →  (more categories?) → loop back
                     →  (all categories done)
                            → decide_followups
                                 → (unmet required skills AND rounds left?)
                                       → generate_followups → back to decide
                                 → (else) → END

The conditional edges and accumulating state (questions, covered categories,
follow-up rounds) are the parts that a plain sequential call cannot express
cleanly. Contrast the report agent, which is a single structured call.
"""

from __future__ import annotations

import json

import structlog
from langgraph.graph import END, StateGraph

from backend.agents.state import GeneratedQuestion, InterviewState
from backend.llms.router import get_llm_router
from backend.prompts.interview.generate import (
    CATEGORY_SYSTEM,
    FOLLOWUP_SYSTEM,
    build_category_prompt,
    build_followup_prompt,
)

logger = structlog.get_logger(__name__)


def _strip_fences(raw: str) -> str:
    """Remove markdown fences from an LLM JSON payload."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else text
        if text.endswith("```"):
            text = text[: text.rfind("```")]
    return text.strip()


def _parse_questions(raw: str, category: str) -> tuple[list[GeneratedQuestion], str | None]:
    """Parse an LLM response into GeneratedQuestion dicts; return (qs, error)."""
    try:
        payload = json.loads(_strip_fences(raw))
    except json.JSONDecodeError as exc:
        return [], f"{category}: invalid JSON ({exc})"
    items = payload.get("questions", [])
    out: list[GeneratedQuestion] = []
    for it in items:
        if not isinstance(it, dict) or "question" not in it:
            continue
        out.append(
            GeneratedQuestion(
                category=category,
                difficulty=str(it.get("difficulty", "medium")),
                question=str(it["question"]),
                expected_answer=it.get("expected_answer"),
                evaluation_criteria=it.get("evaluation_criteria"),
                probes_gap=it.get("probes_gap"),
            )
        )
    return out, None


async def _generate_category(state: InterviewState) -> InterviewState:
    """Node: generate 3 questions for the current category."""
    category = state["current_category"]
    router = get_llm_router()
    prompt = build_category_prompt(
        candidate_name=state["candidate_name"],
        profile_summary=state["profile_summary"],
        job_title=state["job_title"],
        category=category,
        matched_skills=state.get("matched_skills", []),
        missing_required=state.get("missing_required", []),
    )
    try:
        raw, model = await router.complete_json(CATEGORY_SYSTEM, prompt)
    except Exception as exc:  # noqa: BLE001
        return {"errors": [f"{category}: {exc}"], "covered_categories": [category]}
    questions, err = _parse_questions(raw, category)
    update: InterviewState = {
        "questions": questions,
        "covered_categories": [category],
        "model_used": model,
    }
    if err:
        update["errors"] = [err]
    return update


def _next_category(state: InterviewState) -> str:
    """Conditional edge: pick the next uncovered category, or move to followups."""
    covered = set(state.get("covered_categories", []))
    remaining = [c for c in state["target_categories"] if c not in covered]
    if remaining:
        return "generate_category"
    return "decide_followups"


async def _set_next_category(state: InterviewState) -> InterviewState:
    """Node: advance current_category to the next uncovered category."""
    covered = set(state.get("covered_categories", []))
    remaining = [c for c in state["target_categories"] if c not in covered]
    return {"current_category": remaining[0]} if remaining else {}


async def _decide_followups(state: InterviewState) -> InterviewState:
    """Node: no-op marker; routing handled by the conditional edge below."""
    return {}


def _should_followup(state: InterviewState) -> str:
    """Conditional edge: loop into follow-ups if unmet skills and rounds remain."""
    unmet = state.get("missing_required", [])
    rounds = state.get("followup_rounds", 0)
    max_rounds = state.get("max_followup_rounds", 1)
    if unmet and rounds < max_rounds:
        return "generate_followups"
    return END


async def _generate_followups(state: InterviewState) -> InterviewState:
    """Node: generate targeted follow-up probes for unmet required skills."""
    router = get_llm_router()
    already = [q["question"] for q in state.get("questions", [])]
    prompt = build_followup_prompt(
        job_title=state["job_title"],
        missing_required=state.get("missing_required", [])[:3],
        already_asked=already,
    )
    try:
        raw, model = await router.complete_json(FOLLOWUP_SYSTEM, prompt)
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": [f"followup: {exc}"],
            "followup_rounds": state.get("followup_rounds", 0) + 1,
        }
    questions, err = _parse_questions(raw, "followup")
    update: InterviewState = {
        "questions": questions,
        "followup_rounds": state.get("followup_rounds", 0) + 1,
        "model_used": model,
    }
    if err:
        update["errors"] = [err]
    return update


def build_interview_graph():
    """Compile and return the interview LangGraph state machine."""
    graph = StateGraph(InterviewState)
    graph.add_node("generate_category", _generate_category)
    graph.add_node("advance_category", _set_next_category)
    graph.add_node("decide_followups", _decide_followups)
    graph.add_node("generate_followups", _generate_followups)

    graph.set_entry_point("generate_category")
    # After generating a category, decide whether more categories remain.
    graph.add_conditional_edges(
        "generate_category",
        _next_category,
        {"generate_category": "advance_category", "decide_followups": "decide_followups"},
    )
    graph.add_edge("advance_category", "generate_category")
    # After all categories, decide whether to loop into follow-ups.
    graph.add_conditional_edges(
        "decide_followups",
        _should_followup,
        {"generate_followups": "generate_followups", END: END},
    )
    # After a follow-up round, re-evaluate (loops until rounds exhausted).
    graph.add_edge("generate_followups", "decide_followups")
    return graph.compile()


_compiled_graph = None


def get_interview_graph():
    """Return a process-wide compiled interview graph."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_interview_graph()
    return _compiled_graph
