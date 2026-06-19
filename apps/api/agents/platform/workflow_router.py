from agents.base_agent import BaseAgent
from models.schemas import AgentFinding, AgentInput


class WorkflowRouterAgent(BaseAgent):
    slug = "workflow-router"
    name = "Workflow Router"
    category = "platform"
    description = "Selects the workflow template and specialist roster."
    instructions = """
Identify whether the request belongs to HR candidate screening, sales lead
qualification, or engineering change review. Recommend the smallest relevant
specialist roster and list the required artifacts. Do not claim that a workflow
was started unless this agent is running inside the API workflow executor.
"""

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        artifact_types = sorted(
            {str(artifact.get("doc_type", "other")) for artifact in agent_input.artifacts}
        )
        artifact_text = ", ".join(artifact_types) if artifact_types else "none"
        context_count = len(agent_input.context_chunks)
        content = (
            "Routed request to the configured HR Candidate Screening workflow. "
            f"Available artifact types: {artifact_text}. "
            f"Retrieved context chunks available to specialists: {context_count}. "
            "Roster continues with evidence retrieval, HR review specialists, policy review, "
            "and final human-review-gated synthesis."
        )
        if context_count == 0:
            content += " No retrieved context was available yet, so downstream findings must state gaps."

        return AgentFinding(
            agent_name=self.name,
            finding_type="workflow_route",
            severity="info",
            title="Workflow route confirmed",
            content=content,
            evidence_chunk_ids=[],
            confidence=0.75,
            requires_human_review=False,
        )
