import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from db.documents import (
    OrganizationNotFoundError,
    SupabaseDocumentRepository,
    WorkflowNotFoundError,
)
from main import app
from routes.documents import get_document_repository, get_embedding_provider_dep


class FakeDocumentRepository:
    def __init__(
        self,
        *,
        known_workflow: UUID | None = None,
        known_org: UUID | None = None,
    ) -> None:
        self.known_workflow = known_workflow
        self.known_org = known_org
        self.calls: list[dict] = []

    async def store_document(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        if self.known_workflow is not None and kwargs["workflow_id"] != self.known_workflow:
            raise WorkflowNotFoundError(str(kwargs["workflow_id"]))
        return {
            "id": uuid4(),
            "org_id": self.known_org or uuid4(),
            "workflow_id": kwargs["workflow_id"],
            "doc_type": kwargs["doc_type"],
            "filename": kwargs["filename"],
            "mime_type": kwargs["mime_type"],
            "status": "uploaded",
            "created_at": datetime.now(UTC),
        }

    async def store_organization_document(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        if self.known_org is not None and kwargs["org_id"] != self.known_org:
            raise OrganizationNotFoundError(str(kwargs["org_id"]))
        return {
            "id": uuid4(),
            "org_id": kwargs["org_id"],
            "workflow_id": None,
            "doc_type": kwargs["doc_type"],
            "filename": kwargs["filename"],
            "mime_type": kwargs["mime_type"],
            "status": "uploaded",
            "created_at": datetime.now(UTC),
        }

    async def list_organization_documents(self, org_id: UUID) -> list[dict]:
        if self.known_org is not None and org_id != self.known_org:
            return []
        return [
            {
                "id": uuid4(),
                "org_id": org_id,
                "workflow_id": None,
                "doc_type": "policy",
                "filename": "handbook.pdf",
                "mime_type": "application/pdf",
                "status": "uploaded",
                "created_at": datetime.now(UTC),
            }
        ]


def _upload(workflow_id: UUID, repository, **form):
    app.dependency_overrides[get_document_repository] = lambda: repository
    try:
        return TestClient(app).post(f"/workflows/{workflow_id}/documents", **form)
    finally:
        app.dependency_overrides.clear()


def _upload_org(org_id: UUID, repository, **form):
    app.dependency_overrides[get_document_repository] = lambda: repository
    try:
        return TestClient(app).post(f"/knowledge/{org_id}/documents", **form)
    finally:
        app.dependency_overrides.clear()


def _list_org(org_id: UUID, repository):
    app.dependency_overrides[get_document_repository] = lambda: repository
    try:
        return TestClient(app).get(f"/knowledge/{org_id}/documents")
    finally:
        app.dependency_overrides.clear()


def test_upload_document_stores_and_returns_metadata() -> None:
    workflow_id = uuid4()
    repository = FakeDocumentRepository(known_workflow=workflow_id)
    response = _upload(
        workflow_id,
        repository,
        data={"doc_type": "resume"},
        files={"file": ("cv.pdf", b"resume bytes", "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "cv.pdf"
    assert body["status"] == "uploaded"
    assert repository.calls[0]["content"] == b"resume bytes"


def test_upload_organization_document_stores_shared_file() -> None:
    org_id = uuid4()
    repository = FakeDocumentRepository(known_org=org_id)
    response = _upload_org(
        org_id,
        repository,
        data={"doc_type": "policy"},
        files={"file": ("handbook.pdf", b"policy bytes", "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["org_id"] == str(org_id)
    assert body["workflow_id"] is None
    assert body["doc_type"] == "policy"
    assert repository.calls[0]["content"] == b"policy bytes"


def test_list_organization_documents_returns_shared_files() -> None:
    org_id = uuid4()
    response = _list_org(org_id, FakeDocumentRepository(known_org=org_id))
    assert response.status_code == 200
    body = response.json()
    assert body[0]["org_id"] == str(org_id)
    assert body[0]["workflow_id"] is None


def test_upload_rejects_invalid_doc_type() -> None:
    response = _upload(
        uuid4(),
        FakeDocumentRepository(),
        data={"doc_type": "invalid"},
        files={"file": ("cv.pdf", b"bytes", "application/pdf")},
    )
    assert response.status_code == 422


def test_upload_rejects_empty_file() -> None:
    response = _upload(
        uuid4(),
        FakeDocumentRepository(),
        data={"doc_type": "resume"},
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 422


def test_upload_unknown_workflow_returns_404() -> None:
    response = _upload(
        uuid4(),
        FakeDocumentRepository(known_workflow=uuid4()),
        data={"doc_type": "resume"},
        files={"file": ("cv.pdf", b"bytes", "application/pdf")},
    )
    assert response.status_code == 404


def test_upload_unknown_organization_returns_404() -> None:
    response = _upload_org(
        uuid4(),
        FakeDocumentRepository(known_org=uuid4()),
        data={"doc_type": "policy"},
        files={"file": ("handbook.pdf", b"bytes", "application/pdf")},
    )
    assert response.status_code == 404


# --- ingestion wiring (upload schedules parse -> chunk -> embed) ----------


class _StubEmbeddingProvider:
    dimensions = 8

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * self.dimensions for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [0.1] * self.dimensions


class IngestingDocumentRepository(FakeDocumentRepository):
    """Fake repo that also captures the chunks ingestion would persist."""

    def __init__(self, *, content: bytes, **kwargs) -> None:
        super().__init__(**kwargs)
        self._content = content
        self.statuses: list[str] = []
        self.chunks: list[dict] = []

    async def store_document(self, **kwargs) -> dict:
        row = await super().store_document(**kwargs)
        # Ingestion needs storage_path + filename to round-trip the upload.
        row["storage_path"] = f"{kwargs['workflow_id']}/stored-{kwargs['filename']}"
        return row

    async def download_document(self, storage_path: str) -> bytes:
        return self._content

    async def set_document_status(self, document_id, status: str) -> None:
        self.statuses.append(status)

    async def replace_document_chunks(self, *, document_id, org_id, workflow_id, chunks) -> int:
        self.chunks = [
            {
                "org_id": str(org_id),
                "workflow_id": None if workflow_id is None else str(workflow_id),
                **chunk,
            }
            for chunk in chunks
        ]
        return len(self.chunks)


def test_upload_document_schedules_ingestion_into_chunks() -> None:
    workflow_id = uuid4()
    repository = IngestingDocumentRepository(
        known_workflow=workflow_id,
        content=("policy paragraph " * 50).encode("utf-8"),
    )
    app.dependency_overrides[get_document_repository] = lambda: repository
    app.dependency_overrides[get_embedding_provider_dep] = _StubEmbeddingProvider
    try:
        response = TestClient(app).post(
            f"/workflows/{workflow_id}/documents",
            data={"doc_type": "policy"},
            files={"file": ("handbook.txt", repository._content, "text/plain")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    # Background task ran after the response: chunks were embedded and persisted.
    assert repository.statuses == ["parsing", "indexed"]
    assert len(repository.chunks) >= 1
    assert all(c["workflow_id"] == str(workflow_id) for c in repository.chunks)
    assert all(len(c["embedding"]) == 8 for c in repository.chunks)


# --- storage repository logic (no network) -------------------------------


class _FakeResult:
    def __init__(self, data) -> None:
        self.data = data


class _FakeTable:
    def __init__(self, name, store) -> None:
        self._name = name
        self._store = store
        self._insert = None

    def select(self, *_):
        return self

    def eq(self, *_):
        return self

    def is_(self, *_):
        return self

    def limit(self, *_):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def insert(self, row):
        self._insert = row
        return self

    def update(self, values):
        self._store.setdefault("updates", []).append({"table": self._name, "values": values})
        return self

    def delete(self):
        self._store.setdefault("deletes", []).append(self._name)
        return self

    def execute(self):
        if self._insert is not None:
            if self._name == "document_chunks":
                rows = self._insert if isinstance(self._insert, list) else [self._insert]
                self._store["chunk_rows"] = rows
                return _FakeResult(rows)
            row = dict(self._insert)
            row.setdefault("id", str(uuid4()))
            row.setdefault("created_at", datetime.now(UTC).isoformat())
            self._store["inserted"] = row
            return _FakeResult([row])
        if self._name == "workflows":
            return _FakeResult([{"org_id": self._store["org_id"]}])
        if self._name == "organizations":
            return _FakeResult([{"id": self._store["org_id"]}])
        if self._name == "documents":
            return _FakeResult(self._store.get("documents", []))
        return _FakeResult([])


class _FakeBucket:
    def __init__(self, store) -> None:
        self._store = store

    def upload(self, path, file, file_options=None):
        self._store["upload"] = {"path": path, "size": len(file), "options": file_options}
        return {"path": path}


class _FakeStorage:
    def __init__(self, store) -> None:
        self._store = store

    def from_(self, bucket):
        self._store["bucket"] = bucket
        return _FakeBucket(self._store)


class _FakeClient:
    def __init__(self, store) -> None:
        self._store = store
        self.storage = _FakeStorage(store)

    def table(self, name):
        return _FakeTable(name, self._store)


def test_repository_uploads_and_inserts_scoped_row() -> None:
    org_id = str(uuid4())
    workflow_id = uuid4()
    store: dict = {"org_id": org_id}
    repository = SupabaseDocumentRepository(_FakeClient(store), "workflow-documents")

    row = asyncio.run(
        repository.store_document(
            workflow_id=workflow_id,
            doc_type="resume",
            filename="../../etc/My Resume.pdf",
            content=b"hello",
            mime_type="application/pdf",
        )
    )

    assert store["bucket"] == "workflow-documents"
    # Path traversal stripped; key stays flat under the workflow prefix.
    assert store["upload"]["path"].startswith(f"{workflow_id}/")
    assert "/" not in store["upload"]["path"].split(f"{workflow_id}/", 1)[1]
    assert row["org_id"] == org_id
    assert row["size_bytes"] == 5
    assert row["status"] == "uploaded"
    assert len(row["content_hash"]) == 64


def test_repository_uploads_shared_org_file() -> None:
    org_id = uuid4()
    store: dict = {"org_id": str(org_id)}
    repository = SupabaseDocumentRepository(_FakeClient(store), "workflow-documents")

    row = asyncio.run(
        repository.store_organization_document(
            org_id=org_id,
            doc_type="policy",
            filename="../../etc/Policy.pdf",
            content=b"hello",
            mime_type="application/pdf",
        )
    )

    assert store["bucket"] == "workflow-documents"
    assert store["upload"]["path"].startswith(f"{org_id}/shared/")
    assert "/" not in store["upload"]["path"].split(f"{org_id}/shared/", 1)[1]
    assert row["org_id"] == str(org_id)
    assert row["workflow_id"] is None
    assert row["metadata"] == {"scope": "organization"}


def test_repository_lists_shared_org_files_only() -> None:
    org_id = uuid4()
    store: dict = {
        "org_id": str(org_id),
        "documents": [
            {
                "id": str(uuid4()),
                "org_id": str(org_id),
                "workflow_id": None,
                "doc_type": "policy",
                "filename": "handbook.pdf",
                "mime_type": "application/pdf",
                "status": "uploaded",
                "created_at": datetime.now(UTC).isoformat(),
            }
        ],
    }
    repository = SupabaseDocumentRepository(_FakeClient(store), "workflow-documents")

    rows = asyncio.run(repository.list_organization_documents(org_id))

    assert rows == store["documents"]


def test_repository_replace_chunks_scopes_workflow_chunks() -> None:
    store: dict = {"org_id": str(uuid4())}
    repository = SupabaseDocumentRepository(_FakeClient(store), "workflow-documents")
    document_id = uuid4()
    org_id = uuid4()
    workflow_id = uuid4()

    count = asyncio.run(
        repository.replace_document_chunks(
            document_id=document_id,
            org_id=org_id,
            workflow_id=workflow_id,
            chunks=[{"chunk_index": 0, "content": "x", "metadata": {}, "embedding": [0.0]}],
        )
    )

    assert count == 1
    # Existing chunks are cleared before inserting fresh ones.
    assert "document_chunks" in store["deletes"]
    rows = store["chunk_rows"]
    assert rows[0]["document_id"] == str(document_id)
    assert rows[0]["org_id"] == str(org_id)
    assert rows[0]["workflow_id"] == str(workflow_id)


def test_repository_replace_chunks_keeps_shared_chunks_null_scoped() -> None:
    store: dict = {"org_id": str(uuid4())}
    repository = SupabaseDocumentRepository(_FakeClient(store), "workflow-documents")

    count = asyncio.run(
        repository.replace_document_chunks(
            document_id=uuid4(),
            org_id=uuid4(),
            workflow_id=None,
            chunks=[{"chunk_index": 0, "content": "x", "metadata": {}, "embedding": [0.0]}],
        )
    )

    assert count == 1
    # NULL workflow_id makes the chunk visible across every workflow in the org.
    assert store["chunk_rows"][0]["workflow_id"] is None


def test_repository_raises_for_unknown_workflow() -> None:
    store: dict = {"org_id": str(uuid4())}

    class _NoWorkflowClient(_FakeClient):
        def table(self, name):
            table = _FakeTable(name, self._store)
            if name == "workflows":
                table.execute = lambda: _FakeResult([])  # type: ignore[method-assign]
            return table

    repository = SupabaseDocumentRepository(_NoWorkflowClient(store), "workflow-documents")
    try:
        asyncio.run(
            repository.store_document(
                workflow_id=uuid4(),
                doc_type="resume",
                filename="cv.pdf",
                content=b"x",
                mime_type=None,
            )
        )
        raise AssertionError("expected WorkflowNotFoundError")
    except WorkflowNotFoundError:
        pass


def test_repository_raises_for_unknown_organization() -> None:
    store: dict = {"org_id": str(uuid4())}

    class _NoOrganizationClient(_FakeClient):
        def table(self, name):
            table = _FakeTable(name, self._store)
            if name == "organizations":
                table.execute = lambda: _FakeResult([])  # type: ignore[method-assign]
            return table

    repository = SupabaseDocumentRepository(_NoOrganizationClient(store), "workflow-documents")
    try:
        asyncio.run(
            repository.store_organization_document(
                org_id=uuid4(),
                doc_type="policy",
                filename="handbook.pdf",
                content=b"x",
                mime_type=None,
            )
        )
        raise AssertionError("expected OrganizationNotFoundError")
    except OrganizationNotFoundError:
        pass
