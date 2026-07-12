"""Ollama-backed embedder (nomic-embed-text, 768-dim by default)."""

from __future__ import annotations

import httpx
import structlog

from backend.core.config import settings
from backend.embeddings.base import BaseEmbedder, EmbeddingError

logger = structlog.get_logger(__name__)


class OllamaEmbedder(BaseEmbedder):
    """Generates embeddings via a local Ollama server.

    Requires a reachable Ollama process serving ``EMBEDDING_MODEL``. If the
    server is unreachable this raises EmbeddingError rather than degrading
    silently — the caller decides how to record the failed parse.
    """

    def __init__(self) -> None:
        """Capture configuration from settings."""
        self._base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self._model = settings.EMBEDDING_MODEL
        self._timeout = settings.EMBEDDING_TIMEOUT_SECONDS
        self.dimension = settings.EMBEDDING_DIMENSION

    async def _embed_one(self, client: httpx.AsyncClient, text: str) -> list[float]:
        """Embed a single text with an already-open client."""
        try:
            resp = await client.post(
                f"{self._base_url}/api/embeddings",
                json={"model": self._model, "prompt": text},
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            logger.error("embedding_request_failed", error=str(exc))
            raise EmbeddingError(f"Ollama embedding failed: {exc}") from exc

        vector = data.get("embedding")
        if not isinstance(vector, list) or not vector:
            raise EmbeddingError("Ollama returned an empty embedding")
        if len(vector) != self.dimension:
            raise EmbeddingError(
                f"Embedding dimension mismatch: expected {self.dimension}, got {len(vector)}"
            )
        return [float(x) for x in vector]

    async def embed(self, text: str) -> list[float]:
        """Return an embedding vector for a single text."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await self._embed_one(client, text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for a list of texts."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return [await self._embed_one(client, t) for t in texts]
