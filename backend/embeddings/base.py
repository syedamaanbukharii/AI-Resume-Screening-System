"""Abstract embedding-provider interface."""

from __future__ import annotations

import abc


class EmbeddingError(Exception):
    """Raised when an embedding backend fails or is unreachable."""


class BaseEmbedder(abc.ABC):
    """Common interface for text-embedding providers.

    The ``dimension`` attribute lets the vector store validate write shape,
    keeping the pipeline dimension-agnostic (swap models via config only).
    """

    dimension: int

    @abc.abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return an embedding vector for a single text.

        Raises:
            EmbeddingError: On backend failure or dimension mismatch.
        """

    @abc.abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for a list of texts."""
