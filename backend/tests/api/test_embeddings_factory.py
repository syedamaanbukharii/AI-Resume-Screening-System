"""Hermetic tests for embedding provider selection (no model download)."""

from __future__ import annotations

import pytest

from backend.core.config import settings
from backend.embeddings.base import EmbeddingError
from backend.embeddings.factory import get_embedder, reset_embedder


@pytest.fixture(autouse=True)
def _reset():
    """Reset the cached embedder and provider around each test."""
    original = settings.EMBEDDING_PROVIDER
    reset_embedder()
    yield
    settings.EMBEDDING_PROVIDER = original
    reset_embedder()


def test_factory_selects_sentence_transformers() -> None:
    """The default provider yields the in-process embedder class."""
    settings.EMBEDDING_PROVIDER = "sentence_transformers"
    reset_embedder()
    emb = get_embedder()
    assert type(emb).__name__ == "SentenceTransformerEmbedder"


def test_factory_selects_ollama() -> None:
    """The ollama provider yields the Ollama embedder class."""
    settings.EMBEDDING_PROVIDER = "ollama"
    reset_embedder()
    emb = get_embedder()
    assert type(emb).__name__ == "OllamaEmbedder"


def test_factory_rejects_unknown_provider() -> None:
    """An unknown provider raises EmbeddingError."""
    settings.EMBEDDING_PROVIDER = "nonsense"
    reset_embedder()
    with pytest.raises(EmbeddingError):
        get_embedder()


@pytest.mark.asyncio
async def test_sentence_transformer_dimension_contract() -> None:
    """With an injected model, embed honors the dimension and normalization path."""
    from backend.embeddings.sentence_transformer import SentenceTransformerEmbedder

    emb = SentenceTransformerEmbedder()

    class FakeModel:
        def get_sentence_embedding_dimension(self) -> int:
            return 384

        def encode(self, texts, normalize_embeddings, convert_to_numpy):  # noqa: ANN001
            return [[1.0 / (384**0.5)] * 384 for _ in texts]

    emb._model = FakeModel()
    vec = await emb.embed("hello")
    assert len(vec) == 384
    batch = await emb.embed_batch(["a", "b"])
    assert len(batch) == 2 and len(batch[0]) == 384
