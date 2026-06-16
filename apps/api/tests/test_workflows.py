from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from main import app
from models.schemas import WorkflowCreate
from routes.workflows import get_workflow_repository


class FakeWorkflowRepository:
    def __init__(self) -> None:
        self.workflow_id = uuid4()
        self.org_id = uuid4()

    def row(self) -> dict:
        return {
            "id": self.workflow_id,
            "org_id": self.org_id,
            "title": "Candidate review",
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
