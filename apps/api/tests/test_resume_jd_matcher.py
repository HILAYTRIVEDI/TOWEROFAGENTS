"""Unit tests for ResumeJDMatcherAgent."""

import asyncio
from uuid import uuid4

import pytest

from agents.hr.resume_jd_matcher import ResumeJDMatcherAgent
from llm.base import ChatResult
from models.schemas import AgentInput


class _FakeProvider:
    """Minimal ChatProvider stub for unit tests."""

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
        task="Assess candidate against senior engineer role",
        context_chunks=[],
        artifacts=[],
        band_room_id=None,
    )
    defaults.update(kwargs)
    return AgentInput(**defaults)


# ------------------------------------------------------------------
# No provider — must raise
# ------------------------------------------------------------------

def test_no_provider_raises() -> None:
    agent = ResumeJDMatcherAgent()
    with pytest.raises(RuntimeError, match="chat_provider"):
        asyncio.run(agent.run(_make_input()))


# ------------------------------------------------------------------
# Non-mock provider: real analysis path
# ------------------------------------------------------------------

def test_non_mock_provider_returns_finding() -> None:
    provider = _FakeProvider("aiml", "Candidate matches 4 of 5 requirements.")
    agent = ResumeJDMatcherAgent(chat_provider=provider)

    chunk_id = str(uuid4())
    agent_input = _make_input(
        context_chunks=[{"id": chunk_id, "content": "5 years Python experience"}],
        artifacts=[{"filename": "resume.pdf", "doc_type": "resume"}],
    )

    finding = asyncio.run(agent.run(agent_input))

    assert finding.agent_name == "Resume/JD Matcher"
    assert finding.finding_type == "resume_jd_match"
    assert finding.requires_human_review is True
    # Non-mock: confidence > 0 and no placeholder prefix
    assert finding.confidence > 0.0
    assert "[PLACEHOLDER" not in finding.content
    assert "[Mock]" not in finding.title
    # Evidence IDs from context chunks must be collected
    assert chunk_id in finding.evidence_chunk_ids
    # Provider received the system + user messages
    assert len(provider.calls) == 1
    assert provider.calls[0][0]["role"] == "system"
    assert provider.calls[0][1]["role"] == "user"


def test_prompt_labels_resume_and_jd_context_sources() -> None:
    provider = _FakeProvider("aiml", "Candidate matches role evidence.")
    agent = ResumeJDMatcherAgent(chat_provider=provider)

    chunks = [
        {
            "id": str(uuid4()),
            "content": "Candidate has WordPress migration experience.",
            "metadata": {"doc_type": "resume", "filename": "resume.pdf"},
        },
        {
            "id": str(uuid4()),
            "content": "Role requires WordPress and AI orchestration.",
            "metadata": {"doc_type": "jd", "filename": "job-description.pdf"},
        },
    ]

    asyncio.run(agent.run(_make_input(context_chunks=chunks)))

    user_message = provider.calls[0][1]["content"]
    assert "source=resume file=resume.pdf" in user_message
    assert "source=jd file=job-description.pdf" in user_message


# ------------------------------------------------------------------
# Mock provider: must annotate content clearly and set confidence=0
# ------------------------------------------------------------------

def test_mock_provider_annotates_and_requires_review() -> None:
    provider = _FakeProvider("mock", "[mock] No external model was called.")
    agent = ResumeJDMatcherAgent(chat_provider=provider)

    finding = asyncio.run(agent.run(_make_input()))

    assert finding.requires_human_review is True
    assert finding.confidence == 0.0
    assert "[PLACEHOLDER" in finding.content
    assert "[Mock]" in finding.title


# ------------------------------------------------------------------
# Evidence IDs: only IDs actually present in context_chunks are cited
# ------------------------------------------------------------------

def test_evidence_ids_from_context_chunks_only() -> None:
    provider = _FakeProvider("aiml", "Analysis complete.")
    agent = ResumeJDMatcherAgent(chat_provider=provider)

    ids = [str(uuid4()), str(uuid4())]
    chunks = [{"id": ids[0], "content": "foo"}, {"id": ids[1], "content": "bar"}]
    finding = asyncio.run(agent.run(_make_input(context_chunks=chunks)))

    assert set(finding.evidence_chunk_ids) == set(ids)


def test_no_context_chunks_means_empty_evidence_ids() -> None:
    provider = _FakeProvider("aiml", "No context.")
    agent = ResumeJDMatcherAgent(chat_provider=provider)
    finding = asyncio.run(agent.run(_make_input(context_chunks=[])))
    assert finding.evidence_chunk_ids == []
