import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from db.documents import SupabaseDocumentRepository, WorkflowNotFoundError
from main import app
from routes.documents import get_document_repository


class FakeDocumentRepository:
    def __init__(self, *, known_workflow: UUID | None = None) -> None:
        self.known_workflow = known_workflow
        self.calls: list[dict] = []

    async def store_document(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        if self.known_workflow is not None and kwargs["workflow_id"] != self.known_workflow:
            raise WorkflowNotFoundError(str(kwargs["workflow_id"]))
        return {
            "id": uuid4(),
            "workflow_id": kwargs["workflow_id"],
            "filename": kwargs["filename"],
            "mime_type": kwargs["mime_type"],
            "status": "uploaded",
            "created_at": datetime.now(UTC),
        }


def _upload(workflow_id: UUID, repository, **form):
    app.dependency_overrides[get_document_repository] = lambda: repository
    try:
        return TestClient(app).post(f"/workflows/{workflow_id}/documents", **form)
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

    def limit(self, *_):
        return self

    def insert(self, row):
        self._insert = row
        return self

    def execute(self):
        if self._insert is not None:
            row = dict(self._insert)
            row.setdefault("id", str(uuid4()))
            row.setdefault("created_at", datetime.now(UTC).isoformat())
            self._store["inserted"] = row
            return _FakeResult([row])
        if self._name == "workflows":
            return _FakeResult([{"org_id": self._store["org_id"]}])
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
