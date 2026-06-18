from agents.base_agent import BaseAgent
from models.schemas import AgentFinding, AgentInput


class BiasReviewerAgent(BaseAgent):
    slug = "bias-reviewer"
    name = "Bias/Safety Reviewer"
    category = "hr"
    description = "Flags unsupported, sensitive, or potentially biased reasoning."
    instructions = (
        "Audit candidate-screening reasoning for unsupported assumptions, proxy use, "
        "sensitive-trait inference, inconsistent standards, and non-job-related factors. "
        "Recommend corrections and human review; do not rank candidates yourself."
    )

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        if self._chat_provider is None:
            raise RuntimeError(
                "BiasReviewerAgent requires a chat_provider; none was injected."
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
            "- Do NOT introduce protected-trait inferences yourself — only flag existing ones.\n"
            "- Protected traits include: age, gender, race, ethnicity, religion, disability, "
            "pregnancy, national origin, marital status, and any other legally protected class.\n"
            "- Only assess reasoning visible in the provided context. Do not fabricate concerns.\n"
            "- If no bias concerns are found, clearly state that the reviewed reasoning appears "
            "job-related and objective, and set severity to 'info'.\n"
            "- If concerns are found, describe them specifically and set severity to 'warning'.\n"
            "- Always recommend human review for the final hiring decision."
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
            title = "[Mock] Bias review — placeholder, not a real analysis"
            severity = "info"
        else:
            content = result.content
            # Infer severity from content: if model flagged concerns, use warning
            lower = content.lower()
            has_concern = any(
                kw in lower
                for kw in ("concern", "bias", "flag", "warning", "protected", "inappropriate")
            )
            severity = "warning" if has_concern else "info"
            title = "Bias review — concerns flagged" if has_concern else "Bias review — no concerns found"

        return AgentFinding(
            agent_name=self.name,
            finding_type="bias_review",
            severity=severity,
            title=title,
            content=content,
            evidence_chunk_ids=evidence_ids,
            confidence=0.0 if is_mock else 0.7,
            requires_human_review=True,  # MVP: always require human review
        )
