"""Single-call LLM parser producing a validated CandidateProfile."""

from __future__ import annotations

import json

import structlog
from pydantic import ValidationError

from backend.llms.base import LLMError
from backend.llms.router import get_llm_router
from backend.prompts.resume_parser.extract import SYSTEM_PROMPT, build_user_prompt
from backend.resume.schemas import CandidateProfile

logger = structlog.get_logger(__name__)


class ParseError(Exception):
    """Raised when the LLM output cannot be parsed into a CandidateProfile."""


def _strip_fences(raw: str) -> str:
    """Remove markdown code fences if a model wrapped its JSON."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else text
        if text.endswith("```"):
            text = text[: text.rfind("```")]
    return text.strip()


async def parse_resume(resume_text: str) -> tuple[CandidateProfile, str]:
    """Parse resume text into a CandidateProfile via one LLM call.

    Returns:
        (profile, model_name) on success.

    Raises:
        ParseError: If the LLM fails or returns invalid/unshaped JSON.
    """
    router = get_llm_router()
    try:
        raw, model_name = await router.complete_json(
            SYSTEM_PROMPT, build_user_prompt(resume_text)
        )
    except LLMError as exc:
        raise ParseError(f"LLM extraction failed: {exc}") from exc

    try:
        payload = json.loads(_strip_fences(raw))
    except json.JSONDecodeError as exc:
        logger.error("resume_parse_json_error", error=str(exc), sample=raw[:200])
        raise ParseError(f"LLM returned invalid JSON: {exc}") from exc

    try:
        profile = CandidateProfile.model_validate(payload)
    except ValidationError as exc:
        logger.error("resume_parse_validation_error", error=str(exc))
        raise ParseError(f"LLM output failed schema validation: {exc}") from exc

    return profile, model_name
