"""Unit tests for resume pipeline components (no external services)."""

from __future__ import annotations

import json

import pytest

from backend.resume import parser as parser_mod
from backend.resume.extractor import ExtractionError, extract_text
from backend.resume.normalizer import normalize_profile
from backend.resume.schemas import CandidateProfile


def test_extract_txt() -> None:
    """Plain-text extraction returns decoded content."""
    out = extract_text(b"Alice\nEngineer", "txt")
    assert "Alice" in out


def test_extract_unsupported_type() -> None:
    """An unsupported file type raises ExtractionError."""
    with pytest.raises(ExtractionError):
        extract_text(b"x", "rtf")


def test_extract_empty_raises() -> None:
    """Whitespace-only content yields no text and raises."""
    with pytest.raises(ExtractionError):
        extract_text(b"   ", "txt")


def test_normalizer_aliases_and_dedup() -> None:
    """Skill aliases canonicalize and duplicates collapse."""
    p = CandidateProfile(
        full_name="X", technical_skills=["JS", "js", "Python", "py", "K8s"]
    )
    n = normalize_profile(p)
    assert n.technical_skills == ["javascript", "python", "kubernetes"]


def test_normalizer_degrees() -> None:
    """Known degrees canonicalize; unknown pass through."""
    p = CandidateProfile(
        full_name="X",
        education=[{"institution": "MIT", "degree": "B.Tech"}],  # type: ignore[list-item]
    )
    n = normalize_profile(p)
    assert n.education[0].degree == "bachelor of technology"


def test_embedding_text_nonempty() -> None:
    """Embedding text assembly produces content from a profile."""
    p = CandidateProfile(full_name="Jane", summary="ML engineer", technical_skills=["python"])
    assert "Jane" in p.to_embedding_text()
    assert "python" in p.to_embedding_text()


@pytest.mark.asyncio
async def test_parser_valid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """The parser validates well-formed LLM JSON into a profile."""

    class FakeRouter:
        async def complete_json(self, s: str, u: str) -> tuple[str, str]:
            return json.dumps({"full_name": "Jane", "email": "jane@x.io"}), "fake"

    monkeypatch.setattr(parser_mod, "get_llm_router", lambda: FakeRouter())
    profile, model = await parser_mod.parse_resume("text")
    assert profile.full_name == "Jane"
    assert model == "fake"


@pytest.mark.asyncio
async def test_parser_strips_fences(monkeypatch: pytest.MonkeyPatch) -> None:
    """The parser tolerates markdown-fenced JSON."""

    class Fenced:
        async def complete_json(self, s: str, u: str) -> tuple[str, str]:
            return '```json\n{"full_name":"Bob"}\n```', "m"

    monkeypatch.setattr(parser_mod, "get_llm_router", lambda: Fenced())
    profile, _ = await parser_mod.parse_resume("text")
    assert profile.full_name == "Bob"


@pytest.mark.asyncio
async def test_parser_invalid_json_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-JSON LLM output raises ParseError."""

    class Bad:
        async def complete_json(self, s: str, u: str) -> tuple[str, str]:
            return "definitely not json", "m"

    monkeypatch.setattr(parser_mod, "get_llm_router", lambda: Bad())
    with pytest.raises(parser_mod.ParseError):
        await parser_mod.parse_resume("text")
