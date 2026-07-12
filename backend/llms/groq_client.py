"""Groq chat-completion client (online LLM backend)."""

from __future__ import annotations

import httpx
import structlog

from backend.core.config import settings
from backend.llms.base import BaseLLM, LLMError

logger = structlog.get_logger(__name__)

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqClient(BaseLLM):
    """Calls Groq's OpenAI-compatible endpoint with JSON response format."""

    name = "groq"

    def __init__(self) -> None:
        """Capture configuration from settings."""
        self._api_key = settings.GROQ_API_KEY
        self._model = settings.GROQ_MODEL
        self._timeout = settings.GROQ_TIMEOUT_SECONDS

    async def is_available(self) -> bool:
        """Return True if an API key is set and the models endpoint responds."""
        if not self._api_key:
            return False
        try:
            async with httpx.AsyncClient(
                timeout=settings.LLM_HEALTHCHECK_TIMEOUT_SECONDS
            ) as client:
                resp = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        """Request a JSON object completion from Groq."""
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(_GROQ_URL, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.error("groq_request_failed", error=str(exc))
            raise LLMError(f"Groq request failed: {exc}") from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError("Groq returned an unexpected response shape") from exc
