import pytest

import band.run_audit as run_audit
from band.remote_agents import RemoteAgentCredentials
from band.run_audit import WorkflowRoomAuditor
from core.config import Settings
from models.schemas import AgentFinding


def _finding(agent_name: str) -> AgentFinding:
    return AgentFinding(
        agent_name=agent_name,
        finding_type="analysis",
        severity="info",
        title=f"{agent_name} finding",
        content="Candidate evidence was reviewed.",
        confidence=0.8,
        requires_human_review=True,
    )


def _creds() -> list[RemoteAgentCredentials]:
    return [
        RemoteAgentCredentials("resume-jd-matcher", "agent-resume", "key-resume"),
        RemoteAgentCredentials("bias-reviewer", "agent-bias", "key-bias"),
        RemoteAgentCredentials("final-decision", "agent-final", "key-final"),
    ]


def _ordered_findings() -> list[tuple[str, AgentFinding]]:
    return [
        ("resume-jd-matcher", _finding("Resume Matcher")),
        ("bias-reviewer", _finding("Bias Reviewer")),
        ("final-decision", _finding("Final Decision")),
    ]


@pytest.mark.asyncio
async def test_mock_mode_builds_mention_chain_without_network(monkeypatch) -> None:
    calls = []

    async def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return 201, {"data": {"id": "should-not-post"}}

    monkeypatch.setattr(run_audit, "load_specialist_credentials", _creds)
    auditor = WorkflowRoomAuditor(
        Settings(band_mode="mock", band_reviewer_handle="hr-reviewer"),
        http_post=fake_post,
    )

    messages = await auditor.post_discussion(
        room_id="room-1",
        ordered_findings=_ordered_findings(),
    )

    assert calls == []
    assert [message.mode for message in messages] == ["mock", "mock", "mock"]
    assert messages[0].mentions == [{"id": "agent-bias", "kind": "mention"}]
    assert messages[1].mentions == [{"id": "agent-final", "kind": "mention"}]
    assert messages[2].mentions == [{"handle": "hr-reviewer", "kind": "mention"}]


@pytest.mark.asyncio
async def test_real_mode_posts_with_sender_credentials(monkeypatch) -> None:
    calls = []

    async def fake_post(url, *, headers, json):
        calls.append({"url": url, "headers": headers, "json": json})
        return 201, {"data": {"id": f"msg-{len(calls)}", "success": True}}

    monkeypatch.setattr(run_audit, "load_specialist_credentials", _creds)
    auditor = WorkflowRoomAuditor(
        Settings(
            band_mode="sdk",
            band_reviewer_handle="hr-reviewer",
            thenvoi_rest_url="https://band.test/",
        ),
        http_post=fake_post,
    )

    messages = await auditor.post_discussion(
        room_id="room-1",
        ordered_findings=_ordered_findings(),
    )

    assert [message.mode for message in messages] == ["real", "real", "real"]
    assert [message.band_message_id for message in messages] == ["msg-1", "msg-2", "msg-3"]
    assert calls[0]["url"] == "https://band.test/api/v1/agent/chats/room-1/messages"
    assert calls[0]["headers"]["X-API-Key"] == "key-resume"
    assert calls[1]["headers"]["X-API-Key"] == "key-bias"
    assert calls[2]["headers"]["X-API-Key"] == "key-final"
    assert calls[2]["json"]["message"]["mentions"] == [
        {"handle": "hr-reviewer", "kind": "mention"}
    ]


@pytest.mark.asyncio
async def test_real_mode_failure_is_reported_not_raised(monkeypatch) -> None:
    async def fake_post(*args, **kwargs):
        raise RuntimeError("band unavailable")

    monkeypatch.setattr(run_audit, "load_specialist_credentials", _creds)
    auditor = WorkflowRoomAuditor(Settings(band_mode="sdk"), http_post=fake_post)

    messages = await auditor.post_discussion(
        room_id="room-1",
        ordered_findings=_ordered_findings()[:1],
    )

    assert len(messages) == 1
    assert messages[0].mode == "failed"
    assert messages[0].band_message_id is None
    assert messages[0].raw_payload["error"] == "band unavailable"


@pytest.mark.asyncio
async def test_missing_room_is_skipped_without_network(monkeypatch) -> None:
    calls = []

    async def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return 201, {"data": {"id": "should-not-post"}}

    monkeypatch.setattr(run_audit, "load_specialist_credentials", _creds)
    auditor = WorkflowRoomAuditor(Settings(band_mode="sdk"), http_post=fake_post)

    messages = await auditor.post_discussion(
        room_id=None,
        ordered_findings=_ordered_findings()[:1],
    )

    assert calls == []
    assert messages[0].mode == "skipped"
    assert messages[0].band_message_id is None
