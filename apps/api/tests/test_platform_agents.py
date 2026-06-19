import asyncio
from uuid import uuid4

from agents.platform.rag_retriever import RAGRetrieverAgent
from agents.platform.workflow_router import WorkflowRouterAgent
from models.schemas import AgentInput


def _agent_input(**overrides) -> AgentInput:
    payload = {
        "workflow_id": str(uuid4()),
        "org_id": str(uuid4()),
        "task": "Assess candidate against role",
        "artifacts": [{"filename": "resume.pdf", "doc_type": "resume"}],
        "context_chunks": [{"id": str(uuid4()), "content": "Candidate has Python experience."}],
    }
    payload.update(overrides)
    return AgentInput(**payload)


def test_workflow_router_confirms_route_without_fabricating_evidence() -> None:
    finding = asyncio.run(WorkflowRouterAgent().run(_agent_input()))

    assert finding.finding_type == "workflow_route"
    assert finding.severity == "info"
    assert finding.evidence_chunk_ids == []
    assert "HR Candidate Screening" in finding.content


def test_rag_retriever_reports_existing_chunk_ids_only() -> None:
    chunk_id = str(uuid4())
    finding = asyncio.run(
        RAGRetrieverAgent().run(
            _agent_input(context_chunks=[{"id": chunk_id, "content": "Policy context"}])
        )
    )

    assert finding.finding_type == "evidence_pack"
    assert finding.severity == "info"
    assert finding.evidence_chunk_ids == [chunk_id]


def test_rag_retriever_warns_when_no_chunks_available() -> None:
    finding = asyncio.run(RAGRetrieverAgent().run(_agent_input(context_chunks=[])))

    assert finding.severity == "warning"
    assert finding.evidence_chunk_ids == []
    assert "No retrieved chunks" in finding.content
