import asyncio

import pytest

from agents.vendor.compliance_agent import ComplianceAgent
from agents.vendor.finance_agent import FinanceAgent
from agents.vendor.legal_agent import LegalAgent
from agents.vendor.procurement_agent import ProcurementAgent
from agents.vendor.security_agent import SecurityAgent
from agents.vendor.vendor_controller import VendorControllerAgent
from models.schemas import AgentInput

SPECIALISTS = [
    (ProcurementAgent, "procurement-review", "procurement_review"),
    (LegalAgent, "legal-review", "legal_review"),
    (SecurityAgent, "security-review", "security_review"),
    (FinanceAgent, "finance-review", "finance_review"),
    (ComplianceAgent, "compliance-review", "compliance_review"),
]


class _FakeProvider:
    def __init__(self, provider_name: str, content: str) -> None:
        self.provider = provider_name
        self._content = content
        self.calls: list[list[dict]] = []

    async def complete(self, messages):
        self.calls.append(messages)

        class _Result:
            provider = self.provider
            content = self._content

        return _Result()


def _make_input(**kwargs):
    defaults = dict(
        workflow_id="w1",
        org_id="o1",
        task="Review vendor Acme Corp for onboarding.",
        context_chunks=[
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "content": "Vendor master service agreement, net-60 payment terms.",
                "metadata": {"doc_type": "contract", "filename": "msa.pdf"},
            }
        ],
        artifacts=[{"filename": "msa.pdf", "doc_type": "contract"}],
    )
    defaults.update(kwargs)
    return AgentInput(**defaults)


@pytest.mark.parametrize("agent_cls,slug,finding_type", SPECIALISTS)
def test_specialist_metadata(agent_cls, slug, finding_type):
    agent = agent_cls()
    assert agent.slug == slug
    assert agent.category == "vendor"
    assert agent.consumes_prior_findings is False


@pytest.mark.parametrize("agent_cls,slug,finding_type", SPECIALISTS)
def test_no_provider_raises(agent_cls, slug, finding_type):
    agent = agent_cls(chat_provider=None)
    with pytest.raises(RuntimeError, match="chat_provider"):
        asyncio.run(agent.run(_make_input()))


@pytest.mark.parametrize("agent_cls,slug,finding_type", SPECIALISTS)
def test_non_mock_provider_returns_finding(agent_cls, slug, finding_type):
    provider = _FakeProvider("aimlapi", "Specialist analysis body.")
    agent = agent_cls(chat_provider=provider)
    finding = asyncio.run(agent.run(_make_input()))
    assert finding.finding_type == finding_type
    assert finding.evidence_chunk_ids == ["11111111-1111-1111-1111-111111111111"]
    assert finding.requires_human_review is True
    assert "[PLACEHOLDER" not in finding.content


@pytest.mark.parametrize("agent_cls,slug,finding_type", SPECIALISTS)
def test_mock_provider_annotates_and_requires_review(agent_cls, slug, finding_type):
    provider = _FakeProvider("mock", "ignored mock body")
    agent = agent_cls(chat_provider=provider)
    finding = asyncio.run(agent.run(_make_input()))
    assert finding.content.startswith("[PLACEHOLDER")
    assert finding.title.startswith("[Mock]")
    assert finding.confidence == 0.0


@pytest.mark.parametrize("agent_cls,slug,finding_type", SPECIALISTS)
def test_evidence_ids_from_context_chunks_only(agent_cls, slug, finding_type):
    provider = _FakeProvider("aimlapi", "body")
    agent = agent_cls(chat_provider=provider)
    finding = asyncio.run(agent.run(_make_input(context_chunks=[])))
    assert finding.evidence_chunk_ids == []


def _prior_finding(name, body):
    return {
        "agent_name": name,
        "finding_type": "procurement_review",
        "severity": "info",
        "title": f"{name} title",
        "content": body,
        "evidence_chunk_ids": [],
        "confidence": 0.5,
        "requires_human_review": True,
    }


def test_controller_metadata():
    agent = VendorControllerAgent()
    assert agent.slug == "vendor-controller"
    assert agent.category == "vendor"
    assert agent.consumes_prior_findings is True


def test_controller_renders_prior_findings_into_prompt():
    provider = _FakeProvider("aimlapi", "RECOMMENDATION: conditional_approval\nSUMMARY: ok")
    agent = VendorControllerAgent(chat_provider=provider)
    agent_input = _make_input(
        prior_findings=[_prior_finding("Security Agent", "Missing SOC 2 report.")]
    )
    finding = asyncio.run(agent.run(agent_input))
    assert finding.finding_type == "final_decision"
    user_msg = provider.calls[0][1]["content"]
    assert "Security Agent" in user_msg
    assert "Missing SOC 2 report." in user_msg


def test_controller_mock_annotates():
    provider = _FakeProvider("mock", "RECOMMENDATION: approve")
    agent = VendorControllerAgent(chat_provider=provider)
    finding = asyncio.run(agent.run(_make_input(prior_findings=[])))
    assert finding.content.startswith("[PLACEHOLDER")
    assert finding.title.startswith("[Mock]")
    assert finding.confidence == 0.0
