"""Unit tests for FinalDecisionAgent."""

import asyncio
from uuid import uuid4

import pytest

from agents.platform.final_decision import FinalDecisionAgent
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
        task="Synthesize findings into a decision packet",
        context_chunks=[],
        artifacts=[],
        band_room_id=None,
        prior_findings=[],
    )
    defaults.update(kwargs)
    return AgentInput(**defaults)


def test_no_provider_raises() -> None:
    agent = FinalDecisionAgent()
    with pytest.raises(RuntimeError, match="chat_provider"):
        asyncio.run(agent.run(_make_input()))


def test_non_mock_provider_returns_finding() -> None:
    provider = _FakeProvider(
        "aiml",
        "RECOMMENDATION: advance\nSUMMARY: Strong match.\nSTRENGTHS: Python skills.\nGAPS: None.\nNEXT STEPS: Schedule interview.",
    )
    agent = FinalDecisionAgent(chat_provider=provider)

    chunk_id = str(uuid4())
    prior = [
        {"agent_name": "Resume/JD Matcher", "finding_type": "resume_jd_match",
         "title": "Resume/JD match analysis", "content": "Good match on 4/5 requirements."}
    ]
    finding = asyncio.run(agent.run(_make_input(
        context_chunks=[{"id": chunk_id, "content": "Candidate summary"}],
        prior_findings=prior,
    )))

    assert finding.agent_name == "Final Decision Agent"
    assert finding.finding_type == "final_decision"
    assert finding.requires_human_review is True
    assert finding.confidence > 0.0
    assert "[PLACEHOLDER" not in finding.content
    assert "[Mock]" not in finding.title
    assert chunk_id in finding.evidence_chunk_ids
    # prior findings should appear in the user message sent to provider
    assert len(provider.calls) == 1
    user_msg = provider.calls[0][1]["content"]
    assert "Resume/JD Matcher" in user_msg


def test_mock_provider_annotates_and_requires_review() -> None:
    provider = _FakeProvider("mock", "[mock] No external model was called.")
    agent = FinalDecisionAgent(chat_provider=provider)

    finding = asyncio.run(agent.run(_make_input()))

    assert finding.requires_human_review is True
    assert finding.confidence == 0.0
    assert "[PLACEHOLDER" in finding.content
    assert "[Mock]" in finding.title


def test_prior_findings_empty_still_runs() -> None:
    provider = _FakeProvider("aiml", "RECOMMENDATION: human_review_required\nNo prior findings to synthesize.")
    agent = FinalDecisionAgent(chat_provider=provider)
    finding = asyncio.run(agent.run(_make_input(prior_findings=[])))
    assert finding.finding_type == "final_decision"
    assert finding.confidence > 0.0


def test_evidence_ids_from_context_chunks_only() -> None:
    provider = _FakeProvider("aiml", "Synthesis complete.")
    agent = FinalDecisionAgent(chat_provider=provider)
    ids = [str(uuid4()), str(uuid4())]
    chunks = [{"id": ids[0], "content": "foo"}, {"id": ids[1], "content": "bar"}]
    finding = asyncio.run(agent.run(_make_input(context_chunks=chunks)))
    assert set(finding.evidence_chunk_ids) == set(ids)
