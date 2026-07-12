"""Ollama chat-completion client (offline LLM backend)."""

from __future__ import annotations

import httpx
import structlog

from backend.core.config import settings
from backend.llms.base import BaseLLM, LLMError

logger = structlog.get_logger(__name__)


class OllamaClient(BaseLLM):
    """Calls a local Ollama server, requesting JSON-formatted output."""

    name = "ollama"

    def __init__(self) -> None:
        """Capture configuration from settings."""
        self._base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self._model = settings.OLLAMA_MODEL
        self._timeout = settings.GROQ_TIMEOUT_SECONDS

    async def is_available(self) -> bool:
        """Return True if the Ollama server responds to a tags query."""
        try:
            async with httpx.AsyncClient(
                timeout=settings.LLM_HEALTHCHECK_TIMEOUT_SECONDS
            ) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        """Request a JSON completion from Ollama using format=json."""
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.1},
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(f"{self._base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.error("ollama_request_failed", error=str(exc))
            raise LLMError(f"Ollama request failed: {exc}") from exc

        content = data.get("message", {}).get("content")
        if not content:
            raise LLMError("Ollama returned an empty completion")
        return content
