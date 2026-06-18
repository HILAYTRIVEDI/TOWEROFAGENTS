import json

from agents.base_agent import BaseAgent
from models.schemas import AgentFinding, AgentInput


class FinalDecisionAgent(BaseAgent):
    slug = "final-decision"
    name = "Final Decision Agent"
    category = "platform"
    description = "Synthesizes verified findings into a decision packet."
    instructions = (
        "Synthesize only findings and evidence visible in the room. Clearly label "
        "strengths, gaps, unresolved questions, and the recommended human next step. "
        "Never make an autonomous hiring, employment, legal, or other high-impact final "
        "decision."
    )

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        if self._chat_provider is None:
            raise RuntimeError(
                "FinalDecisionAgent requires a chat_provider; none was injected."
            )

        chunk_lines: list[str] = []
        evidence_ids: list[str] = []
        for chunk in agent_input.context_chunks:
            chunk_id = str(chunk.get("id", ""))
            if chunk_id:
                evidence_ids.append(chunk_id)
            snippet = str(chunk.get("content", ""))[:200]
            chunk_lines.append(f"[chunk:{chunk_id}] {snippet}")

        artifact_names = ", ".join(
            f"{a.get('filename','?')} ({a.get('doc_type','?')})"
            for a in agent_input.artifacts
        ) or "none"

        # Render prior findings from specialist agents into the prompt
        prior_block = ""
        if agent_input.prior_findings:
            lines = []
            for pf in agent_input.prior_findings:
                lines.append(
                    f"- [{pf.get('agent_name','?')} / {pf.get('finding_type','?')}] "
                    f"{pf.get('title','?')}: {str(pf.get('content',''))[:400]}"
                )
            prior_block = "\n\nPrior specialist findings:\n" + "\n".join(lines)

        system_msg = (
            f"{self.instructions}\n\n"
            "STRICT GUARDRAILS:\n"
            "- Synthesize ONLY from the provided findings. Do not add external knowledge.\n"
            "- Never fabricate strengths, gaps, or a numerical fit score.\n"
            "- Produce a recommendation of 'advance', 'decline', or 'human_review_required'.\n"
            "- Always recommend human review as the final step for high-impact decisions.\n"
            "- Structure your response with clear sections: "
            "RECOMMENDATION, SUMMARY, STRENGTHS, GAPS, NEXT STEPS."
        )
        user_msg = (
            f"Task: {agent_input.task}\n\n"
            f"Artifacts available: {artifact_names}\n\n"
            f"Retrieved context chunks ({len(chunk_lines)}):\n"
            + ("\n".join(chunk_lines) if chunk_lines else "(none)")
            + prior_block
        )

        result = await self._chat_provider.complete(
            [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]
        )

        is_mock = result.provider == "mock"

        if is_mock:
            content = (
                "[PLACEHOLDER — mock provider was used, no external model was called] "
                f"{result.content}"
            )
            title = "[Mock] Final decision — placeholder, not a real synthesis"
        else:
            content = result.content
            title = "Final decision synthesis"

        return AgentFinding(
            agent_name=self.name,
            finding_type="final_decision",
            severity="info",
            title=title,
            content=content,
            evidence_chunk_ids=evidence_ids,
            confidence=0.0 if is_mock else 0.8,
            requires_human_review=True,  # MVP: always require human review for high-impact decisions
        )
