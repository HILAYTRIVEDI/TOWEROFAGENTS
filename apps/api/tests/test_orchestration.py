import asyncio
from unittest.mock import MagicMock, patch
import pytest
from uuid import uuid4

from core.config import Settings
from workflows.graph import build_workflow_graph, WorkflowState
from workflows.executor import WorkflowExecutor
from models.schemas import AgentInput, AgentFinding
from agents.hr.resume_jd_matcher import ResumeJDMatcherAgent
from fastapi.testclient import TestClient
from main import app


class MockTable:
    def __init__(self, data=None):
        self.data = data or []

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def in_(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def single(self, *args, **kwargs):
        # Allow returning data directly or self depending on context
        return self

    def update(self, *args, **kwargs):
        return self

    def delete(self, *args, **kwargs):
        return self

    def insert(self, *args, **kwargs):
        return self

    def upsert(self, *args, **kwargs):
        return self

    def execute(self):
        mock_response = MagicMock()
        mock_response.data = self.data
        return mock_response


class MockSupabaseClient:
    def __init__(self, workflow_data=None, document_data=None, chunk_data=None, template_data=None):
        self.workflow_data = workflow_data or {}
        self.document_data = document_data or []
        self.chunk_data = chunk_data or []
        self.template_data = template_data or []
        self.table_calls = []

    def table(self, table_name):
        self.table_calls.append(table_name)
        if table_name == "workflows":
            return MockTable(self.workflow_data)
        elif table_name == "documents":
            return MockTable(self.document_data)
        elif table_name == "document_chunks":
            return MockTable(self.chunk_data)
        elif table_name == "workflow_templates":
            return MockTable(self.template_data)
        elif table_name == "agents":
            return MockTable([
                {"id": str(uuid4()), "slug": "resume-jd-matcher"},
                {"id": str(uuid4()), "slug": "bias-reviewer"},
                {"id": str(uuid4()), "slug": "interview-planner"},
                {"id": str(uuid4()), "slug": "policy-guardian"},
                {"id": str(uuid4()), "slug": "final-decision"},
                {"id": str(uuid4()), "slug": "workflow-router"},
                {"id": str(uuid4()), "slug": "rag-retriever"},
                {"id": str(uuid4()), "slug": "lead-qualifier"},
                {"id": str(uuid4()), "slug": "engineering-reviewer"},
            ])
        else:
            return MockTable([])


class MockBandClient:
    def __init__(self):
        self.messages = []

    async def create_room(self, name: str) -> str:
        return f"mock-room-{uuid4()}"

    async def post_message(self, room_id: str, content: str):
        self.messages.append((room_id, content))
        return MagicMock()


@pytest.mark.asyncio
async def test_agent_execution_persists_finding_and_posts_to_band():
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-key",
        llm_provider="mock",
        band_mode="mock"
    )

    mock_supabase = MockSupabaseClient(
        workflow_data={"org_id": str(uuid4()), "title": "HR review"},
    )
    mock_band = MockBandClient()

    with patch("agents.base_agent.get_settings", return_value=settings), \
         patch("agents.base_agent.create_supabase_client", return_value=mock_supabase), \
         patch("agents.base_agent.create_band_client", return_value=mock_band):
        
        agent = ResumeJDMatcherAgent()
        agent_input = AgentInput(
            workflow_id=str(uuid4()),
            org_id=str(uuid4()),
            task="Compare candidate details against job requirements",
            context_chunks=[{"id": str(uuid4()), "content": "Experience in Python system design."}],
            artifacts=[],
            band_room_id="room-abc"
        )
        
        finding = await agent.run(agent_input)
        
        assert isinstance(finding, AgentFinding)
        assert finding.agent_name == "Resume/JD Matcher"
        assert len(mock_band.messages) == 1
        assert "resume-jd-matcher" in mock_supabase.table_calls or "agents" in mock_supabase.table_calls


@pytest.mark.asyncio
async def test_workflow_executor_graph_transitions():
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-key",
        llm_provider="mock",
        band_mode="mock"
    )

    workflow_id = uuid4()
    org_id = uuid4()

    mock_supabase = MockSupabaseClient(
        workflow_data={"id": str(workflow_id), "org_id": str(org_id), "title": "HR review", "user_request": "Screen candidate", "band_room_id": "room-1"},
        document_data=[{"id": str(uuid4()), "filename": "resume.pdf", "doc_type": "resume", "status": "indexed", "storage_path": "resume-path"}],
        chunk_data=[{"id": str(uuid4()), "content": "Python backend experience."}],
        template_data=[{"id": str(uuid4()), "slug": "hr-candidate-screening"}]
    )
    mock_band = MockBandClient()

    with patch("workflows.executor.get_settings", return_value=settings), \
         patch("workflows.executor.create_supabase_client", return_value=mock_supabase), \
         patch("workflows.executor.create_band_client", return_value=mock_band), \
         patch("agents.base_agent.create_supabase_client", return_value=mock_supabase), \
         patch("agents.base_agent.create_band_client", return_value=mock_band):

        executor = WorkflowExecutor()
        initial_state = WorkflowState(
            workflow_id=str(workflow_id),
            org_id=str(org_id),
            user_request="Screen candidate",
            template_slug="hr-candidate-screening",
            band_room_id=None,
            artifacts=[],
            selected_agents=[],
            retrieved_context=[],
            agent_findings=[],
            policy_verdict=None,
            final_report=None,
            status="running"
        )

        final_state = await executor.run(initial_state)
        assert final_state["status"] in {"completed", "awaiting_review"}
        assert len(final_state["agent_findings"]) > 0
        assert "workflow_reports" in mock_supabase.table_calls


def test_run_workflow_endpoint_not_found():
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-key",
    )
    mock_client = MockSupabaseClient(workflow_data=[])  # Empty

    with patch("routes.workflows.create_supabase_client", return_value=mock_client):
        client = TestClient(app)
        response = client.post(f"/workflows/{uuid4()}/run", json={"force_reindex": False})
        assert response.status_code == 404


def test_run_workflow_endpoint_accepted():
    workflow_id = uuid4()
    org_id = uuid4()
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-key",
    )
    mock_client = MockSupabaseClient(workflow_data=[{"id": str(workflow_id), "org_id": str(org_id), "title": "HR screening", "user_request": "Assess candidate", "template_id": str(uuid4())}])

    with patch("routes.workflows.create_supabase_client", return_value=mock_client):
        with patch("workflows.executor.WorkflowExecutor.run") as mock_run:
            client = TestClient(app)
            response = client.post(f"/workflows/{workflow_id}/run", json={"force_reindex": False})
            assert response.status_code == 202
            assert response.json()["status"] == "running"


def test_get_workflow_report_endpoint():
    workflow_id = uuid4()
    org_id = uuid4()
    report_id = uuid4()
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-key",
    )
    
    mock_report = {
        "id": str(report_id),
        "workflow_id": str(workflow_id),
        "org_id": str(org_id),
        "recommendation": "moving forward",
        "summary": "Overall good candidate",
        "fit_score": 85.0,
        "strengths": ["Python"],
        "gaps": ["React"],
        "interview_questions": ["Explain graph logic?"],
        "policy_note": "Compliant",
        "evidence_chunk_ids": [str(uuid4())],
        "requires_human_review": False,
        "report_payload": {}
    }
    
    mock_client = MockSupabaseClient()
    mock_client.table = lambda name: MockTable([mock_report]) if name == "workflow_reports" else MockTable([])

    with patch("routes.workflows.create_supabase_client", return_value=mock_client):
        client = TestClient(app)
        response = client.get(f"/workflows/{workflow_id}/report")
        assert response.status_code == 200
        data = response.json()
        assert data["recommendation"] == "moving forward"
        assert data["fit_score"] == 85.0
