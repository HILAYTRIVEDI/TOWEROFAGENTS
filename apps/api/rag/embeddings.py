"""Embedding providers behind a single typed interface.

The provider is selected by `settings.embedding_provider`. Every provider emits
vectors of exactly `settings.embedding_dimensions` floats, which MUST match the
`vector(N)` dimension declared in the SQL migrations and the
`match_document_chunks` signature.
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol


class EmbeddingProvider(Protocol):
    dimensions: int

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...


class UnconfiguredEmbeddingProvider:
    """Explicit unconfigured state: fails loudly instead of pretending to embed."""

    dimensions = 1536

    def __init__(self, dimensions: int = 1536) -> None:
        self.dimensions = dimensions

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("Embedding provider is not configured")

    async def embed_query(self, text: str) -> list[float]:
        raise RuntimeError("Embedding provider is not configured")


class MockEmbeddingProvider:
    """Deterministic, offline embeddings for tests and unconfigured demos.

    Not a real model: vectors are derived from a content hash so distinct text
    yields distinct (but meaningless) unit vectors. Never present this as a
    production integration.
    """

    def __init__(self, dimensions: int = 1536) -> None:
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Expand the 32-byte digest to the requested dimension, then L2-normalise
        # so cosine similarity behaves sensibly.
        raw = [digest[i % len(digest)] / 255.0 for i in range(self.dimensions)]
        norm = math.sqrt(sum(value * value for value in raw)) or 1.0
        return [value / norm for value in raw]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class OpenAICompatibleEmbeddingProvider:
    """OpenAI-compatible embeddings (OpenAI, AIML API, Featherless).

    All three expose the same `/embeddings` contract, so one async client with a
    configurable base_url covers every real provider.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        dimensions: int,
        base_url: str | None = None,
    ) -> None:
        from openai import AsyncOpenAI

        self.dimensions = dimensions
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]

    async def embed_query(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(model=self._model, input=[text])
        return response.data[0].embedding


def get_embedding_provider(settings) -> EmbeddingProvider:
    """Resolve the embedding provider from settings.

    Falls back to the explicit unconfigured state when a real provider is
    selected but its credentials are missing, so callers fail loudly rather than
    silently producing empty embeddings.
    """

    provider = (settings.embedding_provider or "mock").lower()
    dimensions = settings.embedding_dimensions

    if provider == "mock":
        return MockEmbeddingProvider(dimensions=dimensions)

    if provider in {"openai", "aiml", "featherless"}:
        if provider == "openai":
            api_key = getattr(settings, "openai_api_key", None)
            base_url = None
        elif provider == "aiml":
            api_key = settings.aiml_api_key
            base_url = "https://api.aimlapi.com/v1"
        else:  # featherless
            api_key = settings.featherless_api_key
            base_url = settings.featherless_base_url

        model = settings.embedding_model
        if not api_key or not model:
            return UnconfiguredEmbeddingProvider(dimensions=dimensions)
        return OpenAICompatibleEmbeddingProvider(
            api_key=api_key,
            model=model,
            dimensions=dimensions,
            base_url=base_url,
        )

    return UnconfiguredEmbeddingProvider(dimensions=dimensions)
