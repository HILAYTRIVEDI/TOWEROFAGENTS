from agents.base_agent import BaseAgent
from models.schemas import AgentFinding, AgentInput


class ResumeJDMatcherAgent(BaseAgent):
    slug = "resume-jd-matcher"
    name = "Resume/JD Matcher"
    category = "hr"
    description = "Compares candidate evidence with role requirements."
    instructions = (
        "Compare only job-related requirements with evidence explicitly present in the "
        "resume and job description. Distinguish confirmed matches, gaps, and unknowns. "
        "Do not infer protected or sensitive traits and do not make the hiring decision."
    )

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        if self._chat_provider is None:
            raise RuntimeError(
                "ResumeJDMatcherAgent requires a chat_provider; none was injected."
            )

        # Compact rendering of context chunks (id + first 200 chars of content)
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
            "- Only reference job-related requirements.\n"
            "- Do not infer, mention, or comment on any protected or sensitive trait "
            "(age, gender, race, religion, disability, etc.).\n"
            "- Do not make a hire/no-hire decision — that requires separate human review.\n"
            "- Do not fabricate evidence that is not in the provided context.\n"
            "- Mark any claim as unknown if supporting evidence is absent."
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
            title = "[Mock] Resume/JD match — placeholder, not a real analysis"
        else:
            content = result.content
            title = "Resume/JD match analysis"

        return AgentFinding(
            agent_name=self.name,
            finding_type="resume_jd_match",
            severity="info",
            title=title,
            content=content,
            evidence_chunk_ids=evidence_ids,
            confidence=0.0 if is_mock else 0.5,
            requires_human_review=True,  # always required until final-decision agent is live
        )
