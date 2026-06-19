from agents.base_agent import BaseAgent
from models.schemas import AgentFinding, AgentInput


class RAGRetrieverAgent(BaseAgent):
    slug = "rag-retriever"
    name = "RAG Retriever"
    category = "platform"
    description = "Builds a workflow-scoped evidence pack."
    instructions = """
Assess whether the room contains enough source material for an evidence pack.
Ask for missing artifacts and identify which supplied sources support each
statement. Never imply that retrieval or indexing occurred unless tool output
in the current conversation proves it.
"""

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        evidence_ids: list[str] = []
        for chunk in agent_input.context_chunks:
            chunk_id = str(chunk.get("id", ""))
            if chunk_id:
                evidence_ids.append(chunk_id)

        artifact_types = sorted(
            {str(artifact.get("doc_type", "other")) for artifact in agent_input.artifacts}
        )
        artifact_text = ", ".join(artifact_types) if artifact_types else "none"
        chunk_count = len(agent_input.context_chunks)

        if chunk_count:
            title = "Evidence pack ready"
            severity = "info"
            content = (
                f"Retrieved evidence pack contains {chunk_count} chunk"
                f"{'' if chunk_count == 1 else 's'} from available artifacts "
                f"({artifact_text}). Downstream agents must cite only these chunk IDs "
                "and mark unsupported claims as unknown."
            )
            confidence = 0.8
        else:
            title = "Evidence pack unavailable"
            severity = "warning"
            content = (
                f"No retrieved chunks were available from artifacts ({artifact_text}). "
                "Specialists can still inspect artifact metadata, but substantive claims "
                "must be treated as missing evidence until documents are indexed."
            )
            confidence = 0.2

        return AgentFinding(
            agent_name=self.name,
            finding_type="evidence_pack",
            severity=severity,
            title=title,
            content=content,
            evidence_chunk_ids=evidence_ids,
            confidence=confidence,
            requires_human_review=False,
        )
