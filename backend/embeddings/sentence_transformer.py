"""Local sentence-transformers embedder.

This is the default embedding provider for the containerized stack: it runs
in-process with no external service, so `docker compose up` needs no Ollama for
the vector path. The model (bge-small-en-v1.5, 384-dim, ~130MB) is small enough
to load on a laptop or CI runner, unlike bge-m3 (~2GB).

Loading is lazy and cached: the model is imported and instantiated on first use,
then reused for the process lifetime. The blocking encode call is offloaded to a
thread so it does not stall the event loop.
"""

from __future__ import annotations

import asyncio

import structlog

from backend.core.config import settings
from backend.embeddings.base import BaseEmbedder, EmbeddingError

logger = structlog.get_logger(__name__)


class SentenceTransformerEmbedder(BaseEmbedder):
    """In-process embedder backed by sentence-transformers."""

    def __init__(self) -> None:
        """Capture configuration; the model is loaded lazily on first embed."""
        self._model_name = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self._model = None

    def _load(self):  # type: ignore[no-untyped-def]
        """Load and cache the sentence-transformers model (blocking)."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover
                raise EmbeddingError(
                    "sentence-transformers not installed; set EMBEDDING_PROVIDER=ollama "
                    "or install the package"
                ) from exc
            logger.info("loading_embedding_model", model=self._model_name)
            self._model = SentenceTransformer(self._model_name)
            actual = self._model.get_sentence_embedding_dimension()
            if actual != self.dimension:
                logger.warning(
                    "embedding_dimension_config_mismatch",
                    configured=self.dimension,
                    actual=actual,
                )
                self.dimension = actual
        return self._model

    def _encode(self, texts: list[str]) -> list[list[float]]:
        """Synchronously encode texts to vectors."""
        model = self._load()
        vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return [[float(x) for x in vec] for vec in vectors]

    async def embed(self, text: str) -> list[float]:
        """Return an embedding vector for a single text."""
        result = await asyncio.to_thread(self._encode, [text])
        return result[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for a list of texts."""
        if not texts:
            return []
        return await asyncio.to_thread(self._encode, texts)
