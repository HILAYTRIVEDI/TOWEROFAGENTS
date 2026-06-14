from typing import Protocol


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

