from agents.base_agent import BaseAgent
from models.schemas import AgentFinding, AgentInput

_MOCK_PREFIX = "[PLACEHOLDER — mock provider was used, no external model was called] "

_INSTRUCTIONS = (
    "You are the Controller Agent in an enterprise vendor-onboarding review. "
    "Synthesize the specialist findings into one final recommendation for a human "
    "approver. Weigh procurement, legal, security, finance, and compliance input. "
    "Surface disagreements between specialists rather than hiding them."
)


class VendorControllerAgent(BaseAgent):
    slug = "vendor-controller"
    name = "Controller Agent"
    category = "vendor"
    description = "Synthesizes specialist findings into a final vendor recommendation."
    instructions = _INSTRUCTIONS
    consumes_prior_findings = True

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        if self._chat_provider is None:
            raise RuntimeError("VendorControllerAgent requires a chat_provider")

        prior_lines: list[str] = []
        evidence_ids: list[str] = []
        for finding in agent_input.prior_findings:
            name = finding.get("agent_name", "Specialist")
            title = finding.get("title", "")
            body = str(finding.get("content", ""))[:400]
            prior_lines.append(f"- {name}: {title}\n  {body}")
            for cid in finding.get("evidence_chunk_ids", []) or []:
                if cid not in evidence_ids:
                    evidence_ids.append(str(cid))
        prior_block = "\n".join(prior_lines) or "No specialist findings were produced."

        system_msg = (
            self.instructions
            + "\n\nSTRICT GUARDRAILS:\n"
            "- Begin your answer with a line 'RECOMMENDATION: <value>' where <value> is "
            "exactly one of: approve, reject, conditional_approval, needs_review.\n"
            "- Then provide SUMMARY, KEY RISKS, DISAGREEMENTS, MISSING INFORMATION, and "
            "NEXT ACTIONS sections.\n"
            "- Do not invent evidence. The recommendation is advisory; a human approves."
        )
        user_msg = (
            f"TASK: {agent_input.task}\n\n"
            f"SPECIALIST FINDINGS:\n{prior_block}\n\n"
            "Produce the final vendor recommendation."
        )

        result = await self._chat_provider.complete(
            [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]
        )
        is_mock = result.provider == "mock"

        content = result.content
        title = "Vendor onboarding recommendation"
        if is_mock:
            content = _MOCK_PREFIX + content
            title = "[Mock] " + title

        return AgentFinding(
            agent_name=self.name,
            finding_type="final_decision",
            severity="info",
            title=title,
            content=content,
            evidence_chunk_ids=evidence_ids,
            confidence=0.0 if is_mock else 0.8,
            requires_human_review=True,
        )
