"""Abstract LLM interface for structured extraction."""

from __future__ import annotations

import abc


class LLMError(Exception):
    """Raised when an LLM backend fails or is unreachable."""


class BaseLLM(abc.ABC):
    """Common interface for chat-completion LLM backends.

    Backends must support a JSON-constrained completion so the resume parser
    can request a schema-shaped object in a single call.
    """

    name: str

    @abc.abstractmethod
    async def is_available(self) -> bool:
        """Return True if the backend is reachable within its health timeout."""

    @abc.abstractmethod
    async def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        """Return a raw JSON string from a JSON-constrained completion.

        Args:
            system_prompt: Instruction defining role and output contract.
            user_prompt: The content to reason over (e.g. resume text).

        Returns:
            The model's raw text, expected to be a single JSON object.

        Raises:
            LLMError: If the backend fails or returns nothing.
        """
