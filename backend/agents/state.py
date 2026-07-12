"""Shared state for the interview LangGraph agent."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

import operator


class GeneratedQuestion(TypedDict):
    """A single generated question with metadata."""

    category: str
    difficulty: str
    question: str
    expected_answer: str | None
    evaluation_criteria: str | None
    probes_gap: str | None  # which skill gap / strength this targets


class InterviewState(TypedDict, total=False):
    """State threaded through the interview graph.

    The graph accumulates questions across category rounds and may loop back to
    generate follow-up probes for unmet required skills, so ``questions`` uses
    an additive reducer and ``covered_categories`` tracks progress to avoid
    repetition — the parts that genuinely need a stateful graph.
    """

    # Inputs (set once)
    candidate_name: str
    profile_summary: str
    job_title: str
    required_skills: list[str]
    missing_required: list[str]
    matched_skills: list[str]
    target_categories: list[str]

    # Accumulating outputs
    questions: Annotated[list[GeneratedQuestion], operator.add]
    covered_categories: Annotated[list[str], operator.add]

    # Control
    current_category: str
    followup_rounds: int
    max_followup_rounds: int

    # Diagnostics
    model_used: str
    errors: Annotated[list[str], operator.add]
