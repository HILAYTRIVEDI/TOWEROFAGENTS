from datetime import UTC, datetime
from uuid import UUID, uuid4

import httpx
from fastapi.testclient import TestClient

from core.config import Settings, get_settings
from main import app
from models.schemas import WorkflowCreate
from routes.documents import get_document_repository, get_embedding_provider_dep
from routes.workflows import get_retriever, get_workflow_repository


def _mock_settings() -> Settings:
    """Settings pinned to mock providers so tests are env-independent."""
    return Settings(
        llm_provider="mock",
        embedding_provider="mock",
        band_mode="mock",
        band_default_room_id=None,
        band_reviewer_handle=None,
    )


def _mock_settings_with_band_room() -> Settings:
    return Settings(
        llm_provider="mock",
        embedding_provider="mock",
        band_mode="mock",
        band_default_room_id="room-demo",
        band_reviewer_handle="hr-reviewer",
    )


class FakeWorkflowRepository:
    def __init__(self, *, band_room_id: str | None = None) -> None:
        self.workflow_id = uuid4()
        self.org_id = uuid4()
        self.report_id = uuid4()
        self.statuses: list[str] = []
        self.report: dict | None = None
        self.band_room_id = band_room_id
        self.band_messages: list[dict] = []
        self.agent_findings: list[dict] = []

    def row(self) -> dict:
        return {
            "id": self.workflow_id,
            "org_id": self.org_id,
            "title": "Candidate review",
            "user_request": "Assess candidate against role",
            "template_slug": "hr-candidate-screening",
            "status": "draft",
            "band_room_id": self.band_room_id,
            "created_at": datetime.now(UTC),
        }

    async def create_workflow(self, payload: WorkflowCreate) -> dict:
        row = self.row()
        row["org_id"] = payload.org_id
        row["title"] = payload.title
        row["template_slug"] = payload.template_slug
        row["band_room_id"] = payload.band_room_id
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

    async def update_workflow_band_room(self, workflow_id: UUID, band_room_id: str) -> dict | None:
        if workflow_id != self.workflow_id:
            return None
        self.band_room_id = band_room_id
        return self.row()

    async def save_workflow_report(self, *, workflow: dict, report, payload: dict) -> dict:
        self.report = report.model_dump(mode="json")
        self.report["id"] = self.report_id
        self.report["report_payload"] = payload
        return self.report

    async def get_workflow_report(self, workflow_id: UUID) -> dict | None:
        return self.report if workflow_id == self.workflow_id else None

    async def get_report(self, report_id: UUID) -> dict | None:
        return self.report if report_id == self.report_id else None

    async def save_band_message(self, message: dict) -> dict:
        row = {**message, "id": uuid4(), "created_at": datetime.now(UTC)}
        self.band_messages.append(row)
        return row

    async def get_band_messages(self, workflow_id: UUID) -> list[dict]:
        if workflow_id != self.workflow_id:
            return []
        return self.band_messages

    async def save_agent_finding(self, finding: dict) -> dict:
        row = {**finding, "id": uuid4(), "created_at": datetime.now(UTC)}
        if row["severity"] == "warning":
            row["severity"] = "medium"
        if row["severity"] == "error":
            row["severity"] = "high"
        row["evidence_chunk_ids"] = [str(UUID(str(value))) for value in row["evidence_chunk_ids"]]
        self.agent_findings.append(row)
        return row

    async def get_agent_findings(self, workflow_id: UUID) -> list[dict]:
        if workflow_id != self.workflow_id:
            return []
        return self.agent_findings


class FailingWorkflowRepository(FakeWorkflowRepository):
    async def list_workflows(self, org_id: UUID) -> list[dict]:
        raise httpx.ConnectError("Name or service not known")


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
            {
                "id": uuid4(),
                "org_id": org_id,
                "workflow_id": self.workflow_id,
                "doc_type": "jd",
                "filename": "job-description.pdf",
                "mime_type": "application/pdf",
                "status": "indexed",
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
        call_index = len(self.calls)
        if call_index == 2:
            doc_type = "resume"
            content = "resume context"
        elif call_index == 3:
            doc_type = "jd"
            content = "job description context"
        else:
            doc_type = "policy"
            content = "shared policy context"
        return [
            {
                "id": uuid4(),
                "content": content,
                "metadata": {"doc_type": doc_type, "filename": f"{doc_type}.pdf"},
            }
        ]


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


def test_list_workflows_reports_external_dependency_failure() -> None:
    repository = FailingWorkflowRepository()
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    try:
        response = TestClient(app).get(f"/workflows?org_id={repository.org_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "External service unavailable. Check configured service URLs "
            "and network/DNS connectivity."
        )
    }


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


def test_create_workflow_can_assign_band_room() -> None:
    repository = FakeWorkflowRepository()
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    try:
        created = TestClient(app).post(
            "/workflows",
            json={
                "org_id": str(repository.org_id),
                "title": "New candidate review",
                "user_request": "Assess candidate against role",
                "template_slug": "hr-candidate-screening",
                "band_room_id": "band-room-123",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["band_room_id"] == "band-room-123"


def test_set_workflow_band_session_to_existing_room() -> None:
    repository = FakeWorkflowRepository()
    app.dependency_overrides[get_settings] = _mock_settings
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    try:
        response = TestClient(app).post(
            f"/workflows/{repository.workflow_id}/band-session",
            json={"band_room_id": "separate-band-room"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["band_room_id"] == "separate-band-room"
    assert repository.band_room_id == "separate-band-room"


def test_set_workflow_band_session_can_create_mock_room() -> None:
    repository = FakeWorkflowRepository()
    app.dependency_overrides[get_settings] = _mock_settings
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    try:
        response = TestClient(app).post(
            f"/workflows/{repository.workflow_id}/band-session",
            json={"create_mock_session": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["band_room_id"].startswith("mock-room-")


def test_real_band_session_creation_requires_existing_room_id() -> None:
    repository = FakeWorkflowRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(
        llm_provider="mock",
        embedding_provider="mock",
        band_mode="sdk",
        band_api_key="key",
        band_agent_id="agent",
    )
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    try:
        response = TestClient(app).post(
            f"/workflows/{repository.workflow_id}/band-session",
            json={"create_mock_session": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "paste its room ID" in response.json()["detail"]


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
    assert embedding_provider.queries[0] == "Assess candidate against role"
    assert any("Resume evidence" in query for query in embedding_provider.queries)
    assert any("Job description evidence" in query for query in embedding_provider.queries)
    assert retriever.calls[0]["org_id"] == str(repository.org_id)
    assert retriever.calls[0]["workflow_id"] == str(repository.workflow_id)
    assert len(retriever.calls) == 3
    assert repository.report is not None
    assert repository.report["report_payload"]["retrieved_context_count"] == 3
    # New payload shape from specialist_agents_v1
    payload = repository.report["report_payload"]
    assert payload["execution_mode"] == "specialist_agents_v1"
    assert isinstance(payload["agents_ran"], list)
    assert isinstance(payload["agents_skipped"], list)
    assert any("Resume evidence" in query for query in payload["retrieval_queries"])
    assert any("Job description evidence" in query for query in payload["retrieval_queries"])
    # Mock provider means any_mock is True and requires_human_review is True
    assert payload["any_mock"] is True
    assert payload["band_audit"] == {"room_id": None, "message_count": 0, "modes": {}}
    assert len(repository.agent_findings) == len(payload["agents_ran"])
    assert repository.agent_findings[0]["agent_slug"] == "workflow-router"
    assert repository.agent_findings[0]["content"]
    assert repository.agent_findings[0]["severity"] in {
        "info",
        "low",
        "medium",
        "high",
        "critical",
    }


def test_run_workflow_posts_mock_band_audit_when_room_configured() -> None:
    repository = FakeWorkflowRepository()
    documents = FakeDocumentRepository(repository.org_id, repository.workflow_id)
    embedding_provider = FakeEmbeddingProvider()
    retriever = FakeRetriever()
    app.dependency_overrides[get_settings] = _mock_settings_with_band_room
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    app.dependency_overrides[get_document_repository] = lambda: documents
    app.dependency_overrides[get_embedding_provider_dep] = lambda: embedding_provider
    app.dependency_overrides[get_retriever] = lambda: retriever
    try:
        response = TestClient(app).post(f"/workflows/{repository.workflow_id}/run", json={})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert repository.statuses == ["running", "awaiting_review"]
    payload = repository.report["report_payload"]  # type: ignore[index]
    assert payload["agents_ran"] == [
        "workflow-router",
        "rag-retriever",
        "resume-jd-matcher",
        "bias-reviewer",
        "interview-planner",
        "policy-guardian",
        "final-decision",
    ]
    assert payload["band_audit"] == {
        "room_id": "room-demo",
        "message_count": 7,
        "modes": {"mock": 7},
    }
    assert len(repository.band_messages) == 7
    assert repository.band_messages[0]["band_room_id"] == "room-demo"
    assert repository.band_messages[0]["sender_ref"] == "workflow-router"
    assert repository.band_messages[0]["band_message_id"] is None
    assert repository.band_messages[0]["raw_payload"]["mode"] == "mock"
    assert repository.band_messages[0]["raw_payload"]["mentions"] == [
        {"handle": "rag-retriever", "kind": "mention"}
    ]
    assert repository.band_messages[-1]["sender_ref"] == "final-decision"
    assert repository.band_messages[-1]["raw_payload"]["mentions"] == [
        {"handle": "hr-reviewer", "kind": "mention"}
    ]


def test_get_workflow_messages_and_findings() -> None:
    repository = FakeWorkflowRepository()
    finding_id = uuid4()
    repository.band_messages.append(
        {
            "id": uuid4(),
            "workflow_id": str(repository.workflow_id),
            "band_message_id": None,
            "band_room_id": "room-demo",
            "sender_type": "agent",
            "sender_ref": "workflow-router",
            "content": "@rag-retriever routing complete",
            "message_type": "message",
            "raw_payload": {"mode": "mock"},
            "created_at": datetime.now(UTC),
        }
    )
    repository.agent_findings.append(
        {
            "id": finding_id,
            "workflow_id": str(repository.workflow_id),
            "agent_slug": "workflow-router",
            "finding_type": "routing",
            "severity": "info",
            "title": "Route selected",
            "content": "Full agent reasoning is persisted here.",
            "evidence_chunk_ids": [],
            "confidence": 0.6,
            "requires_human_review": True,
            "raw_output": {"agent_name": "Workflow Router"},
            "created_at": datetime.now(UTC),
        }
    )
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    client = TestClient(app)
    try:
        messages = client.get(f"/workflows/{repository.workflow_id}/messages")
        findings = client.get(f"/workflows/{repository.workflow_id}/findings")
    finally:
        app.dependency_overrides.clear()

    assert messages.status_code == 200
    assert messages.json()[0]["raw_payload"]["mode"] == "mock"
    assert findings.status_code == 200
    assert findings.json()[0]["id"] == str(finding_id)
    assert findings.json()[0]["content"] == "Full agent reasoning is persisted here."


def test_get_missing_workflow_report_returns_not_found() -> None:
    repository = FakeWorkflowRepository()
    app.dependency_overrides[get_workflow_repository] = lambda: repository
    try:
        response = TestClient(app).get(f"/workflows/{repository.workflow_id}/report")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
