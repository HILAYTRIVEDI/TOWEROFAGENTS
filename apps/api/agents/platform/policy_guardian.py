from agents.base_agent import BaseAgent
from models.schemas import AgentFinding, AgentInput


class PolicyGuardianAgent(BaseAgent):
    slug = "policy-guardian"
    name = "Policy Guardian"
    category = "platform"
    description = "Checks findings against policy and escalation rules."
    instructions = (
        "Review proposed findings against policy text supplied in the room. Separate "
        "clear policy conflicts, uncertain interpretations, and missing policy evidence. "
        "Escalate consequential or ambiguous decisions to a human reviewer."
    )

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        if self._chat_provider is None:
            raise RuntimeError(
                "PolicyGuardianAgent requires a chat_provider; none was injected."
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

        system_msg = (
            f"{self.instructions}\n\n"
            "STRICT GUARDRAILS:\n"
            "- Only cite policy text that is present in the provided context or artifacts.\n"
            "- Do not invent policy rules. If policy text is absent, state that explicitly.\n"
            "- Clearly distinguish: (a) clear policy conflicts, (b) uncertain interpretations, "
            "(c) no policy evidence found.\n"
            "- If policy concerns exist, set severity to 'warning'; otherwise 'info'.\n"
            "- Always recommend human escalation for final hiring decisions.\n"
            "OUTPUT FORMAT:\n"
            "- Reply with a single concise policy note of 1-3 plain-text sentences.\n"
            "- Do NOT use markdown, headings, bold (**), bullet points, numbered lists, "
            "or section labels like 'Findings Summary'.\n"
            "- Write it as one short paragraph that a reader can scan in a report card, "
            "for example: 'No policy conflicts found. Skills X and Y are claimed but not "
            "verified in the provided documents. Human review recommended before any "
            "hiring decision.'"
        )
        user_msg = (
            f"Task: {agent_input.task}\n\n"
            f"Artifacts available: {artifact_names}\n\n"
            f"Retrieved context chunks ({len(chunk_lines)}):\n"
            + ("\n".join(chunk_lines) if chunk_lines else "(none)")
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
            title = "[Mock] Policy check — placeholder, not a real policy review"
            severity = "info"
        else:
            content = result.content
            lower = content.lower()
            has_concern = any(
                kw in lower
                for kw in ("conflict", "concern", "violation", "non-compliant", "policy warning", "escalate")
            )
            severity = "warning" if has_concern else "info"
            title = "Policy check — concerns found" if has_concern else "Policy check — compliant"

        return AgentFinding(
            agent_name=self.name,
            finding_type="policy_check",
            severity=severity,
            title=title,
            content=content,
            evidence_chunk_ids=evidence_ids,
            confidence=0.0 if is_mock else 0.7,
            requires_human_review=True,  # MVP: always require human review
        )
