import pytest

from core.config import Settings
from rag.embeddings import (
    MockEmbeddingProvider,
    OpenAICompatibleEmbeddingProvider,
    UnconfiguredEmbeddingProvider,
    get_embedding_provider,
)


class _EmbeddingClient:
    def __init__(self, vectors: list[list[float]]) -> None:
        self.embeddings = self
        self._vectors = vectors

    async def create(self, *, model: str, input: list[str]):
        class _Item:
            def __init__(self, embedding: list[float]) -> None:
                self.embedding = embedding

        class _Response:
            def __init__(self, vectors: list[list[float]]) -> None:
                self.data = [_Item(vector) for vector in vectors]

        return _Response(self._vectors)


def test_get_embedding_provider_configures_openai() -> None:
    provider = get_embedding_provider(
        Settings(
            embedding_provider="openai",
            embedding_model="text-embedding-3-small",
            openai_api_key="test-key",
        )
    )

    assert isinstance(provider, OpenAICompatibleEmbeddingProvider)


def test_get_embedding_provider_fails_loudly_without_real_credentials() -> None:
    provider = get_embedding_provider(
        Settings(
            embedding_provider="aiml",
            embedding_model="text-embedding-3-small",
            aiml_api_key="",
        )
    )

    assert isinstance(provider, UnconfiguredEmbeddingProvider)


@pytest.mark.asyncio
async def test_mock_embedding_provider_returns_configured_dimension() -> None:
    provider = MockEmbeddingProvider(dimensions=8)

    assert len(await provider.embed_query("hello")) == 8
    assert [len(vector) for vector in await provider.embed_documents(["a", "b"])] == [
        8,
        8,
    ]


@pytest.mark.asyncio
async def test_openai_compatible_provider_rejects_wrong_dimension() -> None:
    provider = OpenAICompatibleEmbeddingProvider.__new__(
        OpenAICompatibleEmbeddingProvider
    )
    provider.dimensions = 3
    provider._model = "embedding-model"
    provider._client = _EmbeddingClient([[0.1, 0.2]])

    with pytest.raises(RuntimeError, match="expected 3"):
        await provider.embed_query("hello")
