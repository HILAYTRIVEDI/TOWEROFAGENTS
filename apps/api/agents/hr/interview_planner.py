from agents.base_agent import BaseAgent
from models.schemas import AgentFinding, AgentInput


class InterviewPlannerAgent(BaseAgent):
    slug = "interview-planner"
    name = "Interview Planner"
    category = "hr"
    description = "Creates evidence-linked interview questions for material gaps."
    instructions = (
        "Create concise, job-related interview questions for material evidence gaps. "
        "Link each question to the requirement or uncertainty it tests. Exclude "
        "questions about protected traits, private life, or irrelevant personal data."
    )

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        if self._chat_provider is None:
            raise RuntimeError(
                "InterviewPlannerAgent requires a chat_provider; none was injected."
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
            "- Questions must be strictly job-related and tied to observable, verifiable skills.\n"
            "- Do not ask about age, health, family status, religion, ethnicity, disability, "
            "or any other protected trait.\n"
            "- Format output as a numbered list, e.g.:\n"
            "  1. [Question linked to requirement X]\n"
            "  2. [Question about gap Y]\n"
            "- Include at least 3 questions when gaps are identified.\n"
            "- Do not fabricate requirements not present in the context."
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
            title = "[Mock] Interview plan — placeholder, not real questions"
        else:
            content = result.content
            title = "Interview plan — job-relevant questions"

        return AgentFinding(
            agent_name=self.name,
            finding_type="interview_plan",
            severity="info",
            title=title,
            content=content,
            evidence_chunk_ids=evidence_ids,
            confidence=0.0 if is_mock else 0.7,
            requires_human_review=True,  # MVP: always require human review
        )
