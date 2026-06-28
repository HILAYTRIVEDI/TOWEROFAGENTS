from agents.base_agent import BaseAgent
from models.schemas import AgentFinding, AgentInput

_MOCK_PREFIX = "[PLACEHOLDER — mock provider was used, no external model was called] "

_INSTRUCTIONS = (
    "You are the Legal Agent in an enterprise vendor-onboarding review. Identify "
    "contract risks, unfavorable terms, liability, indemnity, termination, and IP "
    "clauses. Cite only the supplied document excerpts. Flag missing contract "
    "language explicitly."
)


class LegalAgent(BaseAgent):
    slug = "legal-review"
    name = "Legal Agent"
    category = "vendor"
    description = "Reviews contract risks and terms."
    instructions = _INSTRUCTIONS

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        if self._chat_provider is None:
            raise RuntimeError("LegalAgent requires a chat_provider")

        chunk_lines: list[str] = []
        evidence_ids: list[str] = []
        for chunk in agent_input.context_chunks:
            chunk_id = chunk.get("id")
            if chunk_id is None:
                continue
            evidence_ids.append(str(chunk_id))
            metadata = chunk.get("metadata") or {}
            doc_type = metadata.get("doc_type", "document")
            filename = metadata.get("filename", "unknown")
            content = str(chunk.get("content", ""))[:200]
            chunk_lines.append(f"[{chunk_id}] ({doc_type} · {filename}) {content}")

        artifact_names = ", ".join(
            str(a.get("filename", "unknown")) for a in agent_input.artifacts
        ) or "none"

        system_msg = (
            self.instructions
            + "\n\nSTRICT GUARDRAILS:\n"
            "- Cite only the bracketed chunk IDs provided. Never invent citations.\n"
            "- If evidence is missing, say so explicitly under a 'Missing information' note.\n"
            "- Keep the analysis advisory; a human makes the final decision."
        )
        user_msg = (
            f"TASK: {agent_input.task}\n"
            f"ARTIFACTS: {artifact_names}\n"
            f"DOCUMENT EXCERPTS:\n" + ("\n".join(chunk_lines) or "none") + "\n\n"
            "Provide your legal risk assessment."
        )

        result = await self._chat_provider.complete(
            [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]
        )
        is_mock = result.provider == "mock"

        content = result.content
        title = "Legal risk assessment"
        if is_mock:
            content = _MOCK_PREFIX + content
            title = "[Mock] " + title

        return AgentFinding(
            agent_name=self.name,
            finding_type="legal_review",
            severity="info",
            title=title,
            content=content,
            evidence_chunk_ids=evidence_ids,
            confidence=0.0 if is_mock else 0.5,
            requires_human_review=True,
        )
