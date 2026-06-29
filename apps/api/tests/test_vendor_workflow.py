import asyncio

from agents.base_agent import BaseAgent
from models.schemas import AgentFinding, AgentInput
from workflows.executor import WorkflowExecutor


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


class _StaticVendorSpecialist(BaseAgent):
    slug = "procurement-review"
    name = "Procurement Agent"
    category = "vendor"
    description = "Test procurement agent."
    instructions = "noop"

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        return AgentFinding(
            agent_name=self.name,
            finding_type="procurement_review",
            severity="warning",
            title="Missing pricing benchmark",
            content="Pricing benchmark is missing.",
            evidence_chunk_ids=["33333333-3333-3333-3333-333333333333"],
            confidence=0.5,
            requires_human_review=True,
        )


class _StaticVendorController(BaseAgent):
    slug = "vendor-controller"
    name = "Controller Agent"
    category = "vendor"
    description = "Test controller agent."
    instructions = "noop"
    consumes_prior_findings = True

    async def run(self, agent_input: AgentInput) -> AgentFinding:
        return AgentFinding(
            agent_name=self.name,
            finding_type="final_decision",
            severity="info",
            title="[Mock] Vendor onboarding recommendation",
            content="[PLACEHOLDER ...] RECOMMENDATION: approve",
            confidence=0.0,
            requires_human_review=True,
        )


def _vendor_state():
    return {
        "workflow_id": "11111111-1111-1111-1111-111111111111",
        "org_id": "22222222-2222-2222-2222-222222222222",
        "user_request": "Onboard vendor Acme Corp.",
        "template_slug": "vendor-onboarding-review",
        "band_room_id": None,
        "artifacts": [{"filename": "msa.pdf", "doc_type": "contract"}],
        "selected_agents": ["procurement-review", "vendor-controller"],
        "retrieved_context": [
            {
                "id": "33333333-3333-3333-3333-333333333333",
                "content": "Net-60 payment terms, no SOC 2 attached.",
                "metadata": {"doc_type": "contract", "filename": "msa.pdf"},
            }
        ],
        "agent_findings": [],
        "policy_verdict": None,
        "final_report": None,
        "status": "running",
    }


def test_vendor_run_produces_decision_packet_in_payload(monkeypatch):
    from workflows import agent_nodes

    monkeypatch.setitem(
        agent_nodes.AGENT_CLASS_BY_SLUG,
        _StaticVendorSpecialist.slug,
        _StaticVendorSpecialist,
    )
    monkeypatch.setitem(
        agent_nodes.AGENT_CLASS_BY_SLUG,
        _StaticVendorController.slug,
        _StaticVendorController,
    )

    executor = WorkflowExecutor(settings=None)
    result = asyncio.run(executor.run(_vendor_state()))
    packet = result["payload"].get("decision_packet")
    assert packet is not None
    assert packet["recommendation"] == "needs_review"
    assert packet["human_approval_required"] is True
    assert [f["agent_name"] for f in packet["agent_findings"]] == [
        "Procurement Agent",
        "Controller Agent",
    ]
    assert packet["audit_trail"]["template_slug"] == "vendor-onboarding-review"


def test_vendor_agents_registered():
    from agents.registry import AGENT_CLASS_BY_SLUG

    for slug in (
        "procurement-review",
        "legal-review",
        "security-review",
        "finance-review",
        "compliance-review",
        "vendor-controller",
    ):
        assert slug in AGENT_CLASS_BY_SLUG


def test_vendor_template_registered():
    from workflows.templates import get_template

    template = get_template("vendor-onboarding-review")
    assert template.agent_slugs[0] == "workflow-router"
    assert "vendor-controller" in template.agent_slugs
    assert "contract" in template.required_artifacts
