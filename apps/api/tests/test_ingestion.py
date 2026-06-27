import asyncio
from uuid import uuid4

from rag.ingestion import index_document


class FakeEmbeddingProvider:
    """Deterministic provider that returns one vector per text."""

    def __init__(self, dimensions: int = 8) -> None:
        self.dimensions = dimensions
        self.batches: list[list[str]] = []

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.batches.append(texts)
        return [[float(len(text) % 7)] * self.dimensions for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [0.0] * self.dimensions


class FakeIngestionStore:
    """In-memory stand-in for the Supabase-backed ingestion store."""

    def __init__(self, content: bytes) -> None:
        self._content = content
        self.statuses: list[str] = []
        self.chunks: list[dict] = []

    async def download_document(self, storage_path: str) -> bytes:
        return self._content

    async def set_document_status(self, document_id, status: str) -> None:
        self.statuses.append(status)

    async def replace_document_chunks(
        self, *, document_id, org_id, workflow_id, chunks
    ) -> int:
        self.chunks = [
            {
                "document_id": str(document_id),
                "org_id": str(org_id),
                "workflow_id": None if workflow_id is None else str(workflow_id),
                **chunk,
            }
            for chunk in chunks
        ]
        return len(self.chunks)


_TEXT = ("policy paragraph " * 50).encode("utf-8")


def _document(*, workflow_id):
    return {
        "id": uuid4(),
        "org_id": uuid4(),
        "workflow_id": workflow_id,
        "storage_path": "org/shared/abc-policy.txt",
        "filename": "policy.txt",
        "doc_type": "policy",
    }


def test_index_document_creates_chunks_for_workflow_document() -> None:
    document = _document(workflow_id=uuid4())
    store = FakeIngestionStore(_TEXT)
    provider = FakeEmbeddingProvider(dimensions=8)

    result = asyncio.run(
        index_document(document, store=store, embedding_provider=provider)
    )

    assert result.status == "indexed"
    assert result.chunk_count >= 1
    assert len(store.chunks) == result.chunk_count
    # Workflow-scoped chunks carry the owning workflow id.
    assert all(c["workflow_id"] == str(document["workflow_id"]) for c in store.chunks)
    assert all(c["metadata"]["doc_type"] == "policy" for c in store.chunks)
    assert all(c["metadata"]["filename"] == "policy.txt" for c in store.chunks)
    assert all(len(c["embedding"]) == 8 for c in store.chunks)
    assert store.statuses == ["parsing", "indexed"]


def test_index_document_creates_shared_chunks_for_org_document() -> None:
    # Shared knowledge-base docs have no workflow; chunks must be workflow_id NULL
    # so match_document_chunks returns them across every workflow in the org.
    document = _document(workflow_id=None)
    store = FakeIngestionStore(_TEXT)
    provider = FakeEmbeddingProvider(dimensions=8)

    result = asyncio.run(
        index_document(document, store=store, embedding_provider=provider)
    )

    assert result.status == "indexed"
    assert result.chunk_count >= 1
    assert all(c["workflow_id"] is None for c in store.chunks)
    assert all(c["org_id"] == str(document["org_id"]) for c in store.chunks)


def test_index_document_marks_failed_on_parse_error() -> None:
    document = _document(workflow_id=None)
    document["filename"] = "data.exe"  # unsupported -> parse_document raises ValueError
    store = FakeIngestionStore(_TEXT)
    provider = FakeEmbeddingProvider()

    try:
        asyncio.run(index_document(document, store=store, embedding_provider=provider))
        raise AssertionError("expected ingestion to raise on unsupported type")
    except ValueError:
        pass

    assert store.statuses[-1] == "failed"
    assert store.chunks == []
