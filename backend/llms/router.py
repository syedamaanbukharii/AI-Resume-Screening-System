"""Model router: selects Groq (online) or Ollama/Gemma (offline)."""

from __future__ import annotations

import structlog

from backend.core.config import settings
from backend.llms.base import BaseLLM, LLMError
from backend.llms.groq_client import GroqClient
from backend.llms.ollama_client import OllamaClient

logger = structlog.get_logger(__name__)


class LLMRouter:
    """Chooses an LLM backend per the configured mode.

    Modes:
        online  — always Groq.
        offline — always Ollama.
        auto    — Groq if reachable within the health timeout, else Ollama.
    """

    def __init__(self) -> None:
        """Instantiate both backends; selection happens per call."""
        self._groq = GroqClient()
        self._ollama = OllamaClient()

    async def select(self) -> BaseLLM:
        """Return the backend to use, honoring mode and availability."""
        mode = settings.LLM_MODE.lower()
        if mode == "online":
            return self._groq
        if mode == "offline":
            return self._ollama

        # auto
        if await self._groq.is_available():
            logger.info("llm_router_selected", backend="groq")
            return self._groq
        logger.info("llm_router_selected", backend="ollama", reason="groq_unavailable")
        return self._ollama

    async def complete_json(self, system_prompt: str, user_prompt: str) -> tuple[str, str]:
        """Complete a JSON request, returning (raw_json, backend_name).

        Raises:
            LLMError: If the selected backend fails.
        """
        backend = await self.select()
        raw = await backend.complete_json(system_prompt, user_prompt)
        return raw, backend.name


_router: LLMRouter | None = None


def get_llm_router() -> LLMRouter:
    """Return a process-wide router singleton."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
