"""Embedder factory: selects the embedding provider from configuration.

Providers:
    sentence_transformers — in-process, no external service (compose/CI default).
    ollama                — nomic-embed via a local Ollama server (fully offline).

The pipeline imports ``get_embedder`` from here rather than from a specific
provider module, so switching providers is a config change only.
"""

from __future__ import annotations

from backend.core.config import settings
from backend.embeddings.base import BaseEmbedder, EmbeddingError

_embedder: BaseEmbedder | None = None


def get_embedder() -> BaseEmbedder:
    """Return a process-wide embedder singleton chosen by provider config."""
    global _embedder
    if _embedder is None:
        provider = settings.EMBEDDING_PROVIDER.lower()
        if provider in {"sentence_transformers", "sentence-transformers", "local"}:
            from backend.embeddings.sentence_transformer import SentenceTransformerEmbedder

            _embedder = SentenceTransformerEmbedder()
        elif provider == "ollama":
            from backend.embeddings.nomic_embed import OllamaEmbedder

            _embedder = OllamaEmbedder()
        else:
            raise EmbeddingError(f"Unsupported embedding provider: {provider}")
    return _embedder


def reset_embedder() -> None:
    """Clear the cached embedder (used in tests)."""
    global _embedder
    _embedder = None
