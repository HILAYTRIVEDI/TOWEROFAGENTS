import os
import pytest
from unittest.mock import MagicMock, patch
from core.config import Settings
from rag.embeddings import get_embedding_provider, OpenAIEmbeddingProvider, MockEmbeddingProvider


def test_get_embedding_provider_case_insensitive() -> None:
    settings = Settings(
        embedding_provider="AiMl",
        aiml_api_key="aiml-key",
        embedding_dimensions=512,
    )
    provider = get_embedding_provider(settings)
    assert isinstance(provider, OpenAIEmbeddingProvider)
    assert provider.dimensions == 512


def test_get_embedding_provider_unknown_raises_error() -> None:
    settings = Settings(
        embedding_provider="unknown-provider",
    )
    with pytest.raises(ValueError, match="Unknown embedding provider: unknown-provider"):
        get_embedding_provider(settings)


def test_get_embedding_provider_openai_missing_env_key() -> None:
    settings = Settings(
        embedding_provider="openai",
    )
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY environment variable is not configured"):
            get_embedding_provider(settings)


def test_get_embedding_provider_openai_with_env_key() -> None:
    settings = Settings(
        embedding_provider="openai",
        embedding_dimensions=1536,
        embedding_model="text-embedding-3-small",
    )
    with patch.dict(os.environ, {"OPENAI_API_KEY": "openai-key"}):
        provider = get_embedding_provider(settings)
        assert isinstance(provider, OpenAIEmbeddingProvider)
        assert provider.dimensions == 1536
        assert provider.model == "text-embedding-3-small"


@pytest.mark.asyncio
async def test_openai_embedding_provider_empty_list() -> None:
    # If texts list is empty, OpenAIEmbeddingProvider should return [] immediately
    # without calling the AsyncOpenAI API.
    provider = OpenAIEmbeddingProvider(
        api_key="test-key",
        model="test-model",
        base_url="https://api.example.com",
    )
    res = await provider.embed_documents([])
    assert res == []


def test_get_embedding_provider_featherless_custom_url() -> None:
    settings = Settings(
        embedding_provider="featherless",
        featherless_api_key="feather-key",
        featherless_base_url="https://custom-featherless.ai/v1",
        embedding_dimensions=1024,
    )
    provider = get_embedding_provider(settings)
    assert isinstance(provider, OpenAIEmbeddingProvider)
    assert provider.dimensions == 1024
