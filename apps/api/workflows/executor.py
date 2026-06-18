from typing import Any
from uuid import uuid4

from models.schemas import WorkflowReportRead
from workflows.graph import WorkflowState


class WorkflowExecutor:
    async def run(self, state: WorkflowState) -> dict[str, Any]:
        workflow_docs = [
            artifact
            for artifact in state["artifacts"]
            if artifact.get("workflow_id") is not None
            and str(artifact.get("workflow_id")) == state["workflow_id"]
        ]
        shared_docs = [
            artifact
            for artifact in state["artifacts"]
            if artifact.get("workflow_id") is None
        ]
        indexed_docs = [
            artifact
            for artifact in state["artifacts"]
            if artifact.get("status") == "indexed"
        ]
        retrieved_context = state["retrieved_context"]

        summary = (
            "MVP workflow run created a review packet from the current workflow "
            f"metadata and document inventory. It found {len(workflow_docs)} "
            f"workflow file(s), {len(shared_docs)} shared Knowledge file(s), and "
            f"{len(indexed_docs)} indexed file(s). Retrieval returned "
            f"{len(retrieved_context)} relevant chunk(s). Specialist agent execution and "
            "LLM synthesis are not enabled yet, so this report requires human review."
        )

        report = WorkflowReportRead(
            id=uuid4(),
            workflow_id=state["workflow_id"],
            recommendation="human_review_required",
            summary=summary,
            strengths=[],
            gaps=[
                "Specialist agents have not executed for this workflow yet.",
                "No evidence chunk IDs were cited because this MVP run does not synthesize retrieved content.",
            ],
            interview_questions=[],
            policy_note="Human review is required before any high-impact decision.",
            evidence_chunk_ids=[],
            requires_human_review=True,
        )
        return {
            "report": report,
            "payload": {
                "selected_agents": state["selected_agents"],
                "document_counts": {
                    "workflow": len(workflow_docs),
                    "shared_knowledge": len(shared_docs),
                    "indexed": len(indexed_docs),
                },
                "retrieved_context_count": len(retrieved_context),
                "retrieved_chunk_ids": [
                    str(chunk["id"]) for chunk in retrieved_context if chunk.get("id")
                ],
                "execution_mode": "mvp_review_packet",
            },
        }
