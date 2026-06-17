from typing import Protocol
from openai import AsyncOpenAI
from core.config import Settings


class EmbeddingProvider(Protocol):
    dimensions: int

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...


class UnconfiguredEmbeddingProvider:
    dimensions = 1536

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("Embedding provider is not configured")

    async def embed_query(self, text: str) -> list[float]:
        raise RuntimeError("Embedding provider is not configured")


class MockEmbeddingProvider:
    def __init__(self, dimensions: int = 1536) -> None:
        self.dimensions = dimensions

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # ponytail: returns deterministic mock embeddings of length dimensions for each text
        return [[0.1] * self.dimensions for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        # ponytail: returns deterministic mock embedding of length dimensions
        return [0.1] * self.dimensions


class OpenAIEmbeddingProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        dimensions: int = 1536,
    ) -> None:
        self.dimensions = dimensions
        self.model = model
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self._client.embeddings.create(
            input=texts,
            model=self.model,
        )
        return [item.embedding for item in response.data]

    async def embed_query(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            input=text,
            model=self.model,
        )
        return response.data[0].embedding


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    provider = settings.embedding_provider.lower()
    dimensions = settings.embedding_dimensions

    if provider == "mock":
        return MockEmbeddingProvider(dimensions=dimensions)
    elif provider == "aiml":
        if not settings.aiml_api_key:
            raise RuntimeError("AIML_API_KEY is not configured")
        model = settings.embedding_model or "text-embedding-3-small"
        return OpenAIEmbeddingProvider(
            api_key=settings.aiml_api_key,
            model=model,
            base_url="https://api.aimlapi.com/v1",
            dimensions=dimensions,
        )
    elif provider == "featherless":
        if not settings.featherless_api_key:
            raise RuntimeError("FEATHERLESS_API_KEY is not configured")
        model = settings.embedding_model or "text-embedding-3-small"
        return OpenAIEmbeddingProvider(
            api_key=settings.featherless_api_key,
            model=model,
            base_url=settings.featherless_base_url,
            dimensions=dimensions,
        )
    elif provider == "openai":
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not configured")
        model = settings.embedding_model or "text-embedding-3-small"
        return OpenAIEmbeddingProvider(
            api_key=api_key,
            model=model,
            dimensions=dimensions,
        )
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


