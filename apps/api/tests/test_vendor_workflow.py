import asyncio

from agents.base_agent import BaseAgent
from models.schemas import AgentFinding, AgentInput


class _PriorFindingsSpy(BaseAgent):
    slug = "prior-findings-spy"
    name = "Prior Findings Spy"
    category = "platform"
    description = "Test agent that records the prior_findings it received."
    instructions = "noop"
    consumes_prior_findings = True

    def __init__(self, chat_provider=None) -> None:
        super().__init__(chat_provider)
        self.seen_prior: list[dict] = []

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        self.seen_prior = list(agent_input.prior_findings)
        return AgentFinding(
            agent_name=self.name,
            finding_type="final_decision",
            severity="info",
            title="spy",
            content="spy",
        )


def test_base_agent_defaults_to_not_consuming_prior_findings():
    assert BaseAgent.consumes_prior_findings is False


def test_node_passes_prior_findings_to_consuming_agent(monkeypatch):
    from workflows import agent_nodes

    spy = _PriorFindingsSpy()
    monkeypatch.setitem(agent_nodes.AGENT_CLASS_BY_SLUG, spy.slug, lambda chat_provider=None: spy)

    node = agent_nodes.make_agent_node(spy.slug, router=None)
    state = {
        "workflow_id": "w1",
        "org_id": "o1",
        "user_request": "review",
        "artifacts": [],
        "retrieved_context": [],
        "band_room_id": None,
        "agent_findings": [
            {
                "agent_name": "Procurement Agent",
                "finding_type": "procurement_review",
                "severity": "info",
                "title": "prior",
                "content": "prior body",
                "evidence_chunk_ids": [],
                "confidence": 0.5,
                "requires_human_review": True,
            }
        ],
    }
    asyncio.run(node(state))
    assert spy.seen_prior and spy.seen_prior[0]["title"] == "prior"
