"""Unit tests for PolicyGuardianAgent."""

import asyncio
from uuid import uuid4

import pytest

from agents.platform.policy_guardian import PolicyGuardianAgent
from llm.base import ChatResult
from models.schemas import AgentInput


class _FakeProvider:
    def __init__(self, provider_name: str, content: str) -> None:
        self.provider = provider_name
        self._content = content
        self.calls: list = []

    async def complete(self, messages, model=None) -> ChatResult:
        self.calls.append(messages)
        return ChatResult(content=self._content, provider=self.provider, model=model or self.provider)


def _make_input(**kwargs) -> AgentInput:
    defaults = dict(
        workflow_id=str(uuid4()),
        org_id=str(uuid4()),
        task="Check assessment against hiring policy",
        context_chunks=[],
        artifacts=[],
        band_room_id=None,
    )
    defaults.update(kwargs)
    return AgentInput(**defaults)


def test_no_provider_raises() -> None:
    agent = PolicyGuardianAgent()
    with pytest.raises(RuntimeError, match="chat_provider"):
        asyncio.run(agent.run(_make_input()))


def test_non_mock_provider_returns_finding() -> None:
    provider = _FakeProvider("aiml", "Assessment is compliant with hiring policy. No conflicts found.")
    agent = PolicyGuardianAgent(chat_provider=provider)

    chunk_id = str(uuid4())
    finding = asyncio.run(agent.run(_make_input(
        context_chunks=[{"id": chunk_id, "content": "Policy: all candidates must have equal opportunity"}],
        artifacts=[{"filename": "policy.pdf", "doc_type": "policy"}],
    )))

    assert finding.agent_name == "Policy Guardian"
    assert finding.finding_type == "policy_check"
    assert finding.requires_human_review is True
    assert finding.confidence > 0.0
    assert "[PLACEHOLDER" not in finding.content
    assert "[Mock]" not in finding.title
    assert chunk_id in finding.evidence_chunk_ids
    assert len(provider.calls) == 1
    assert provider.calls[0][0]["role"] == "system"
    assert provider.calls[0][1]["role"] == "user"


def test_mock_provider_annotates_and_requires_review() -> None:
    provider = _FakeProvider("mock", "[mock] No external model was called.")
    agent = PolicyGuardianAgent(chat_provider=provider)

    finding = asyncio.run(agent.run(_make_input()))

    assert finding.requires_human_review is True
    assert finding.confidence == 0.0
    assert "[PLACEHOLDER" in finding.content
    assert "[Mock]" in finding.title


def test_warning_severity_when_policy_concern() -> None:
    provider = _FakeProvider("aiml", "There is a policy conflict: candidate was not given equal review opportunity.")
    agent = PolicyGuardianAgent(chat_provider=provider)
    finding = asyncio.run(agent.run(_make_input()))
    assert finding.severity == "warning"


def test_info_severity_when_compliant() -> None:
    provider = _FakeProvider("aiml", "Assessment is compliant. No issues detected.")
    agent = PolicyGuardianAgent(chat_provider=provider)
    finding = asyncio.run(agent.run(_make_input()))
    assert finding.severity == "info"


def test_evidence_ids_from_context_chunks_only() -> None:
    provider = _FakeProvider("aiml", "Policy check complete.")
    agent = PolicyGuardianAgent(chat_provider=provider)
    ids = [str(uuid4()), str(uuid4())]
    chunks = [{"id": ids[0], "content": "policy text"}, {"id": ids[1], "content": "more policy"}]
    finding = asyncio.run(agent.run(_make_input(context_chunks=chunks)))
    assert set(finding.evidence_chunk_ids) == set(ids)
