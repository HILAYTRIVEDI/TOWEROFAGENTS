from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from core.config import Settings, get_settings
from main import app
from models.schemas import WorkflowCreate
from routes.documents import get_document_repository, get_embedding_provider_dep
from routes.workflows import get_retriever, get_workflow_repository


def _mock_settings() -> Settings:
    """Settings pinned to mock providers so tests are env-independent."""
    return Settings(llm_provider="mock", embedding_provider="mock")


class FakeWorkflowRepository:
    def __init__(self) -> None:
        self.workflow_id = uuid4()
        self.org_id = uuid4()
        self.report_id = uuid4()
        self.statuses: list[str] = []
        self.report: dict | None = None

    def row(self) -> dict:
        return {
            "id": self.workflow_id,
            "org_id": self.org_id,
            "title": "Candidate review",
            "user_request": "Assess candidate against role",
            "template_slug": "hr-candidate-screening",
            "status": "draft",
            "band_room_id": None,
            "created_at": datetime.now(UTC),
        }

    async def create_workflow(self, payload: WorkflowCreate) -> dict:
        row = self.row()
        row["org_id"] = payload.org_id
        row["title"] = payload.title
        row["template_slug"] = payload.template_slug
        return row

    async def list_workflows(self, org_id: UUID) -> list[dict]:
        return [self.row()] if org_id == self.org_id else []

    async def get_workflow(self, workflow_id: UUID) -> dict | None:
        return self.row() if workflow_id == self.workflow_id else None

    async def delete_workflow(self, workflow_id: UUID) -> bool:
        return workflow_id == self.workflow_id

    async def update_workflow_status(self, workflow_id: UUID, status: str) -> None:
        if workflow_id == self.workflow_id:
            self.statuses.append(status)

    async def save_workflow_report(self, *, workflow: dict, report, payload: dict) -> dict:
        self.report = report.model_dump(mode="json")
        self.report["id"] = self.report_id
        self.report["report_payload"] = payload
        return self.report

    async def get_workflow_report(self, workflow_id: UUID) -> dict | None:
        return self.report if workflow_id == self.workflow_id else None

    async def get_report(self, report_id: UUID) -> dict | None:
        return self.report if report_id == self.report_id else None


class FakeDocumentRepository:
    def __init__(self, org_id: UUID, workflow_id: UUID) -> None:
        self.org_id = org_id
        self.workflow_id = workflow_id

    async def list_organization_documents(self, org_id: UUID) -> list[dict]:
        if org_id != self.org_id:
            return []
        return [
            {
                "id": uuid4(),
                "org_id": org_id,
                "workflow_id": None,
                "doc_type": "policy",
                "filename": "handbook.pdf",
                "mime_type": "application/pdf",
                "status": "indexed",
                "created_at": datetime.now(UTC),
            },
            {
                "id": uuid4(),
                "org_id": org_id,
                "workflow_id": self.workflow_id,
                "doc_type": "resume",
                "filename": "resume.pdf",
                "mime_type": "application/pdf",
                "status": "uploaded",
                "created_at": datetime.now(UTC),
            },
        ]


class FakeEmbeddingProvider:
    dimensions = 2

    def __init__(self) -> None:
        self.queries: list[str] = []

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2] for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        self.queries.append(text)
        return [0.1, 0.2]


class FakeRetriever:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def search(self, **kwargs) -> list[dict]:
        self.calls.append(kwargs)
        return [{"id": uuid4(), "content": "shared policy context"}]


def test_list_workflows_without_org_scope_is_empty() -> None:
    repository = FakeWorkflowRepository()
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    try:
        response = TestClient(app).get("/workflows")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []


def test_list_workflows_is_org_scoped() -> None:
    repository = FakeWorkflowRepository()
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    try:
        response = TestClient(app).get(f"/workflows?org_id={repository.org_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Candidate review"


def test_create_and_get_workflow() -> None:
    repository = FakeWorkflowRepository()
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    client = TestClient(app)
    try:
        created = client.post(
            "/workflows",
            json={
                "org_id": str(repository.org_id),
                "title": "New candidate review",
                "user_request": "Assess candidate against role",
                "template_slug": "hr-candidate-screening",
            },
        )
        fetched = client.get(f"/workflows/{repository.workflow_id}")
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["title"] == "New candidate review"
    assert fetched.status_code == 200


def test_delete_workflow_returns_no_content() -> None:
    repository = FakeWorkflowRepository()
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    try:
        response = TestClient(app).delete(f"/workflows/{repository.workflow_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""


def test_delete_missing_workflow_returns_not_found() -> None:
    repository = FakeWorkflowRepository()
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    try:
        response = TestClient(app).delete(f"/workflows/{uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_run_workflow_persists_review_report() -> None:
    repository = FakeWorkflowRepository()
    documents = FakeDocumentRepository(repository.org_id, repository.workflow_id)
    embedding_provider = FakeEmbeddingProvider()
    retriever = FakeRetriever()
    app.dependency_overrides[get_settings] = _mock_settings
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    app.dependency_overrides[get_document_repository] = lambda: documents
    app.dependency_overrides[get_embedding_provider_dep] = lambda: embedding_provider
    app.dependency_overrides[get_retriever] = lambda: retriever
    client = TestClient(app)
    try:
        run = client.post(f"/workflows/{repository.workflow_id}/run", json={})
        workflow_report = client.get(f"/workflows/{repository.workflow_id}/report")
        report = client.get(f"/reports/{repository.report_id}")
    finally:
        app.dependency_overrides.clear()

    assert run.status_code == 202
    assert run.json()["status"] == "awaiting_review"
    assert run.json()["report_id"] == str(repository.report_id)
    assert repository.statuses == ["running", "awaiting_review"]
    assert workflow_report.status_code == 200
    assert workflow_report.json()["recommendation"] == "human_review_required"
    assert workflow_report.json()["requires_human_review"] is True
    assert report.status_code == 200
    # With specialist_agents_v1 executor and mock provider, the summary reflects
    # agent run counts and mock provider usage — not the old MVP packet strings.
    summary = report.json()["summary"]
    assert "human_review_required" in report.json()["recommendation"]
    assert report.json()["requires_human_review"] is True
    # Embedding + retrieval plumbing must still be exercised
    assert embedding_provider.queries == ["Assess candidate against role"]
    assert retriever.calls[0]["org_id"] == str(repository.org_id)
    assert retriever.calls[0]["workflow_id"] == str(repository.workflow_id)
    assert repository.report is not None
    assert repository.report["report_payload"]["retrieved_context_count"] == 1
    # New payload shape from specialist_agents_v1
    payload = repository.report["report_payload"]
    assert payload["execution_mode"] == "specialist_agents_v1"
    assert isinstance(payload["agents_ran"], list)
    assert isinstance(payload["agents_skipped"], list)
    # Mock provider means any_mock is True and requires_human_review is True
    assert payload["any_mock"] is True


def test_get_missing_workflow_report_returns_not_found() -> None:
    repository = FakeWorkflowRepository()
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    try:
        response = TestClient(app).get(f"/workflows/{repository.workflow_id}/report")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
