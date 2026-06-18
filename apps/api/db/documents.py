import asyncio
import hashlib
import re
from typing import Any, Protocol
from uuid import UUID, uuid4

# Storage object keys are derived from user-supplied filenames, so strip
# anything outside this set to keep the key flat (no path traversal, no "/").
_UNSAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


class WorkflowNotFoundError(LookupError):
    """Raised when a document is uploaded against an unknown workflow."""


class OrganizationNotFoundError(LookupError):
    """Raised when a document is uploaded against an unknown organization."""


class DocumentRepository(Protocol):
    async def store_document(
        self,
        *,
        workflow_id: UUID,
        doc_type: str,
        filename: str,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, Any]: ...

    async def store_organization_document(
        self,
        *,
        org_id: UUID,
        doc_type: str,
        filename: str,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, Any]: ...

    async def list_organization_documents(self, org_id: UUID) -> list[dict[str, Any]]: ...

    async def list_workflow_documents(self, workflow_id: UUID) -> list[dict[str, Any]]: ...

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


def _safe_object_name(filename: str) -> str:
    base = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    cleaned = _UNSAFE_NAME.sub("_", base).strip("._")
    return cleaned or "upload"


class SupabaseDocumentRepository:
    def __init__(self, client: Any, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    async def store_document(
        self,
        *,
        workflow_id: UUID,
        doc_type: str,
        filename: str,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, Any]:
        return await asyncio.to_thread(
            self._store_document, workflow_id, doc_type, filename, content, mime_type
        )

    async def store_organization_document(
        self,
        *,
        org_id: UUID,
        doc_type: str,
        filename: str,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, Any]:
        return await asyncio.to_thread(
            self._store_organization_document, org_id, doc_type, filename, content, mime_type
        )

    async def list_organization_documents(self, org_id: UUID) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._list_organization_documents, org_id)

    async def list_workflow_documents(self, workflow_id: UUID) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._list_workflow_documents, workflow_id)

    async def download_document(self, storage_path: str) -> bytes:
        return await asyncio.to_thread(self._download_document, storage_path)

    async def set_document_status(self, document_id: Any, status: str) -> None:
        await asyncio.to_thread(self._set_document_status, document_id, status)

    async def replace_document_chunks(
        self,
        *,
        document_id: Any,
        org_id: Any,
        workflow_id: Any | None,
        chunks: list[dict[str, Any]],
    ) -> int:
        return await asyncio.to_thread(
            self._replace_document_chunks, document_id, org_id, workflow_id, chunks
        )

    def _store_document(
        self,
        workflow_id: UUID,
        doc_type: str,
        filename: str,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, Any]:
        # Resolve org scope from the owning workflow; the documents row requires
        # org_id and we never trust a client-supplied org.
        workflow = (
            self._client.table("workflows")
            .select("org_id")
            .eq("id", str(workflow_id))
            .limit(1)
            .execute()
        )
        if not workflow.data:
            raise WorkflowNotFoundError(str(workflow_id))
        org_id = workflow.data[0]["org_id"]

        storage_path = f"{workflow_id}/{uuid4().hex}-{_safe_object_name(filename)}"
        content_hash = hashlib.sha256(content).hexdigest()

        # upsert=false: never silently overwrite an existing object; the uuid
        # prefix already makes collisions effectively impossible.
        self._client.storage.from_(self._bucket).upload(
            path=storage_path,
            file=content,
            file_options={
                "content-type": mime_type or "application/octet-stream",
                "upsert": "false",
            },
        )

        inserted = (
            self._client.table("documents")
            .insert(
                {
                    "org_id": org_id,
                    "workflow_id": str(workflow_id),
                    "doc_type": doc_type,
                    "filename": filename,
                    "storage_path": storage_path,
                    "mime_type": mime_type,
                    "size_bytes": len(content),
                    "content_hash": content_hash,
                    "status": "uploaded",
                }
            )
            .execute()
        )
        if not inserted.data:
            raise RuntimeError("Supabase document insert returned no data")
        return inserted.data[0]

    def _store_organization_document(
        self,
        org_id: UUID,
        doc_type: str,
        filename: str,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, Any]:
        organization = (
            self._client.table("organizations")
            .select("id")
            .eq("id", str(org_id))
            .limit(1)
            .execute()
        )
        if not organization.data:
            raise OrganizationNotFoundError(str(org_id))

        storage_path = f"{org_id}/shared/{uuid4().hex}-{_safe_object_name(filename)}"
        content_hash = hashlib.sha256(content).hexdigest()

        self._client.storage.from_(self._bucket).upload(
            path=storage_path,
            file=content,
            file_options={
                "content-type": mime_type or "application/octet-stream",
                "upsert": "false",
            },
        )

        inserted = (
            self._client.table("documents")
            .insert(
                {
                    "org_id": str(org_id),
                    "workflow_id": None,
                    "doc_type": doc_type,
                    "filename": filename,
                    "storage_path": storage_path,
                    "mime_type": mime_type,
                    "size_bytes": len(content),
                    "content_hash": content_hash,
                    "status": "uploaded",
                    "metadata": {"scope": "organization"},
                }
            )
            .execute()
        )
        if not inserted.data:
            raise RuntimeError("Supabase document insert returned no data")
        return inserted.data[0]

    def _list_organization_documents(self, org_id: UUID) -> list[dict[str, Any]]:
        response = (
            self._client.table("documents")
            .select("id,org_id,workflow_id,doc_type,filename,mime_type,status,created_at")
            .eq("org_id", str(org_id))
            .is_("workflow_id", "null")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

    def _list_workflow_documents(self, workflow_id: UUID) -> list[dict[str, Any]]:
        # Ingestion needs storage_path + filename; org scope comes from the row so
        # chunks stay tenant-scoped without trusting client input.
        response = (
            self._client.table("documents")
            .select("id,org_id,workflow_id,filename,storage_path,status")
            .eq("workflow_id", str(workflow_id))
            .execute()
        )
        return response.data or []

    def _download_document(self, storage_path: str) -> bytes:
        return self._client.storage.from_(self._bucket).download(storage_path)

    def _set_document_status(self, document_id: Any, status: str) -> None:
        (
            self._client.table("documents")
            .update({"status": status})
            .eq("id", str(document_id))
            .execute()
        )

    def _replace_document_chunks(
        self,
        document_id: Any,
        org_id: Any,
        workflow_id: Any | None,
        chunks: list[dict[str, Any]],
    ) -> int:
        # Re-indexing is idempotent: drop the document's existing chunks first so a
        # re-upload never leaves stale vectors behind.
        (
            self._client.table("document_chunks")
            .delete()
            .eq("document_id", str(document_id))
            .execute()
        )
        if not chunks:
            return 0

        rows = [
            {
                "document_id": str(document_id),
                "org_id": str(org_id),
                # NULL workflow_id marks an org-shared chunk that match_document_chunks
                # returns across every workflow in the organization.
                "workflow_id": None if workflow_id is None else str(workflow_id),
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],
                "metadata": chunk.get("metadata") or {},
                "embedding": chunk["embedding"],
            }
            for chunk in chunks
        ]
        self._client.table("document_chunks").insert(rows).execute()
        return len(rows)
