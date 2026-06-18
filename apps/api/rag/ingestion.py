"""Document ingestion: parse -> chunk -> embed -> persist scoped chunks.

Handles both workflow-scoped documents (workflow_id set) and organization-shared
knowledge-base documents (workflow_id is None). Shared chunks are stored with a
NULL workflow_id so `match_document_chunks` (migration 004) returns them across
every workflow in the organization.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol

from rag.chunker import chunk_text
from rag.embeddings import EmbeddingProvider
from rag.parser import parse_document

logger = logging.getLogger(__name__)


class IngestionStore(Protocol):
    """Storage operations ingestion needs, isolated for testability."""

    async def download_document(self, storage_path: str) -> bytes: ...

    async def set_document_status(self, document_id: Any, status: str) -> None: ...

    async def replace_document_chunks(
        self,
        *,
        document_id: Any,
        org_id: Any,
        workflow_id: Any | None,
        chunks: list[dict[str, Any]],
    ) -> int: ...


@dataclass(frozen=True)
class IngestionResult:
    document_id: str
    chunk_count: int
    status: str


async def index_document(
    document: dict[str, Any],
    *,
    store: IngestionStore,
    embedding_provider: EmbeddingProvider,
) -> IngestionResult:
    """Index a single stored document into `document_chunks`.

    `document` is a row from `public.documents` carrying at least id, org_id,
    workflow_id (may be None), storage_path and filename. Status transitions:
    parsing -> indexed on success, parsing -> failed on any error.
    """

    document_id = document["id"]
    org_id = document["org_id"]
    workflow_id = document.get("workflow_id")  # None for shared org docs
    storage_path = document["storage_path"]
    filename = document["filename"]

    await store.set_document_status(document_id, "parsing")
    try:
        content = await store.download_document(storage_path)
        parsed = parse_document(filename, content)
        chunks = chunk_text(parsed.text, parsed.metadata)

        records: list[dict[str, Any]] = []
        if chunks:
            embeddings = await embedding_provider.embed_documents(
                [chunk.content for chunk in chunks]
            )
            records = [
                {
                    "chunk_index": chunk.index,
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                    "embedding": embedding,
                }
                for chunk, embedding in zip(chunks, embeddings, strict=True)
            ]

        count = await store.replace_document_chunks(
            document_id=document_id,
            org_id=org_id,
            workflow_id=workflow_id,
            chunks=records,
        )
        await store.set_document_status(document_id, "indexed")
        # Confidential content: log only counts and identifiers, never chunk text.
        logger.info("Indexed document %s into %d chunks", document_id, count)
        return IngestionResult(str(document_id), count, "indexed")
    except Exception:
        await store.set_document_status(document_id, "failed")
        logger.exception("Failed to index document %s", document_id)
        raise


async def run_ingestion_safely(
    document: dict[str, Any],
    *,
    store: IngestionStore,
    embedding_provider: EmbeddingProvider,
) -> None:
    """Background-task entrypoint: index a document, swallowing failures.

    Ingestion runs after the upload response is sent, so an exception here must
    not crash the request lifecycle. A failure is already recorded as
    `status = failed` on the document row (see `index_document`) and surfaced via
    the document read endpoints, so we log and return rather than propagate.
    """

    try:
        await index_document(
            document, store=store, embedding_provider=embedding_provider
        )
    except Exception:
        # Already logged with a stack trace inside index_document.
        logger.warning(
            "Background ingestion did not complete for document %s",
            document.get("id"),
        )
