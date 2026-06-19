"""Conversational @mention audit poster for workflow runs.

Each specialist posts one Band message as its OWN identity (X-API-Key),
@mentioning the next agent in the run order. The final agent @mentions a
configured reviewer. This is a genuine REST integration with an explicit mock
fallback — it never fabricates success or exposes secrets.

Public interface (stable — backend run-path depends on this):

    from band.run_audit import WorkflowRoomAuditor, PostedBandMessage

    auditor = WorkflowRoomAuditor(settings)
    messages: list[PostedBandMessage] = await auditor.post_discussion(
        room_id=workflow.band_room_id,
        ordered_findings=[(slug, finding), ...],
    )

PostedBandMessage fields
------------------------
sender_slug       str            slug of the posting agent
sender_agent_id   str | None     Band UUID of the posting agent (None in mock)
content           str            message text including @handles
mentions          list[dict]     mention objects sent to Band
band_message_id   str | None     Band-assigned message id (None when not "real")
mode              str            "real" | "mock" | "failed" | "skipped"
raw_payload       dict           sanitized metadata (no secrets): mode,
                                 http_status, error, recipients

Mode semantics
--------------
"real"    — HTTP 2xx received; band_message_id populated
"mock"    — band_mode != "sdk" or creds missing; no network call made
"skipped" — room_id is falsy; no network call made
"failed"  — network error, non-2xx, or httpx unavailable; never raises
"""

from __future__ import annotations

import logging
import textwrap
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from band.remote_agents import RemoteAgentCredentials, load_specialist_credentials
from core.config import Settings
from models.schemas import AgentFinding

logger = logging.getLogger(__name__)

# Band REST base default — matches coordinator.py DEFAULT_THENVOI_REST_URL.
_DEFAULT_REST_URL = "https://app.band.ai/"

_PLACEHOLDER_MARKER = "[PLACEHOLDER"
_CONTENT_MAX = 200


@dataclass
class PostedBandMessage:
    sender_slug: str
    sender_agent_id: str | None
    content: str
    mentions: list[dict]
    band_message_id: str | None
    mode: str  # "real" | "mock" | "failed" | "skipped"
    raw_payload: dict = field(default_factory=dict)


def _one_line_summary(finding: AgentFinding) -> str:
    """Return a short single-line summary from title + trimmed content."""
    title = finding.title.strip()
    body = finding.content.replace("\n", " ").strip()
    combined = f"{title} — {body}" if body else title
    summary = textwrap.shorten(combined, width=_CONTENT_MAX, placeholder="…")
    if finding.content.startswith(_PLACEHOLDER_MARKER) or finding.confidence == 0.0:
        return f"[PLACEHOLDER] {summary}"
    return summary


def _rest_url(settings: Settings) -> str:
    base = (settings.thenvoi_rest_url or _DEFAULT_REST_URL).rstrip("/")
    return base


def _messages_url(rest_base: str, room_id: str) -> str:
    return f"{rest_base}/api/v1/agent/chats/{room_id}/messages"


class WorkflowRoomAuditor:
    """Posts one @mention message per specialist finding to the Band room.

    http_post is injectable for testing without network:
        async def http_post(url, *, headers, json) -> (status_code, body_dict)
    When None the default path imports httpx lazily and degrades to "failed"
    mode if httpx is unavailable.
    """

    def __init__(
        self,
        settings: Settings,
        http_post: Callable[..., Coroutine[Any, Any, tuple[int, dict]]] | None = None,
    ) -> None:
        self._settings = settings
        self._http_post = http_post or _default_http_post
        # {slug: credentials} — built once; empty means no real posting possible.
        creds_list = load_specialist_credentials()
        self._creds: dict[str, RemoteAgentCredentials] = {c.slug: c for c in creds_list}

    async def post_discussion(
        self,
        *,
        room_id: str | None,
        ordered_findings: list[tuple[str, AgentFinding]],
    ) -> list[PostedBandMessage]:
        """Post one message per (slug, finding) pair; never raises."""
        if not ordered_findings:
            return []

        rest_base = _rest_url(self._settings)
        results: list[PostedBandMessage] = []
        n = len(ordered_findings)

        for i, (slug, finding) in enumerate(ordered_findings):
            is_last = i == n - 1
            creds = self._creds.get(slug)

            # Build the mention target for this sender.
            mention, next_slug = self._build_mention(i, ordered_findings, is_last)

            summary = _one_line_summary(finding)
            at_label = f"@{next_slug}" if next_slug else "@reviewer"
            content = f"{at_label} {finding.agent_name}: {summary}"

            msg = await self._post_one(
                room_id=room_id,
                creds=creds,
                slug=slug,
                content=content,
                mention=mention,
                rest_base=rest_base,
            )
            results.append(msg)

        return results

    def _build_mention(
        self,
        i: int,
        ordered_findings: list[tuple[str, AgentFinding]],
        is_last: bool,
    ) -> tuple[dict, str]:
        """Return (mention_object, display_slug) for the agent at position i."""
        n = len(ordered_findings)
        settings = self._settings

        if not is_last:
            next_slug, _ = ordered_findings[i + 1]
            next_creds = self._creds.get(next_slug)
            if next_creds:
                return {"id": next_creds.agent_id, "kind": "mention"}, next_slug
            return {"handle": next_slug, "kind": "mention"}, next_slug

        # Last agent: reviewer > coordinator > first roster member.
        if settings.band_reviewer_handle:
            return {"handle": settings.band_reviewer_handle, "kind": "mention"}, settings.band_reviewer_handle

        if settings.band_agent_id:
            return {"id": settings.band_agent_id, "kind": "mention"}, "coordinator"

        # Last resort: first agent in roster (guaranteed participant).
        first_slug, _ = ordered_findings[0]
        first_creds = self._creds.get(first_slug)
        if first_creds:
            return {"id": first_creds.agent_id, "kind": "mention"}, first_slug
        return {"handle": first_slug, "kind": "mention"}, first_slug

    async def _post_one(
        self,
        *,
        room_id: str | None,
        creds: RemoteAgentCredentials | None,
        slug: str,
        content: str,
        mention: dict,
        rest_base: str,
    ) -> PostedBandMessage:
        agent_id = creds.agent_id if creds else None

        # Decide mode before any network call.
        if not room_id:
            logger.info("[mock-band] skipped post for %s (no room_id)", slug)
            return PostedBandMessage(
                sender_slug=slug,
                sender_agent_id=agent_id,
                content=content,
                mentions=[mention],
                band_message_id=None,
                mode="skipped",
                raw_payload={"mode": "skipped"},
            )

        if self._settings.band_mode != "sdk" or not creds:
            reason = "band_mode != sdk" if self._settings.band_mode != "sdk" else "no credentials"
            logger.info("[mock-band] %s | %s: %s", slug, reason, content)
            return PostedBandMessage(
                sender_slug=slug,
                sender_agent_id=agent_id,
                content=content,
                mentions=[mention],
                band_message_id=None,
                mode="mock",
                raw_payload={"mode": "mock", "reason": reason},
            )

        # Attempt real POST.
        url = _messages_url(rest_base, room_id)
        headers = {"X-API-Key": creds.api_key, "Content-Type": "application/json"}
        body = {"message": {"content": content, "mentions": [mention]}}

        try:
            status, data = await self._http_post(url, headers=headers, json=body)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[band] POST failed for %s: %s", slug, exc)
            return PostedBandMessage(
                sender_slug=slug,
                sender_agent_id=agent_id,
                content=content,
                mentions=[mention],
                band_message_id=None,
                mode="failed",
                raw_payload={"mode": "failed", "error": str(exc)},
            )

        if status < 200 or status >= 300:
            logger.warning("[band] POST %s returned HTTP %s for %s", url, status, slug)
            return PostedBandMessage(
                sender_slug=slug,
                sender_agent_id=agent_id,
                content=content,
                mentions=[mention],
                band_message_id=None,
                mode="failed",
                raw_payload={"mode": "failed", "http_status": status, "error": str(data)},
            )

        band_id = (data.get("data") or {}).get("id")
        recipients = (data.get("data") or {}).get("recipients", [])
        logger.info("[band] posted for %s → message_id=%s", slug, band_id)
        return PostedBandMessage(
            sender_slug=slug,
            sender_agent_id=agent_id,
            content=content,
            mentions=[mention],
            band_message_id=band_id,
            mode="real",
            raw_payload={"mode": "real", "http_status": status, "recipients": recipients},
        )


async def _default_http_post(
    url: str, *, headers: dict, json: dict
) -> tuple[int, dict]:
    """Default HTTP poster using httpx. Degrades to RuntimeError if httpx is absent."""
    try:
        import httpx  # lazy import — already in requirements.txt
    except ImportError as exc:
        raise RuntimeError(
            "httpx is required for real Band posting but is not installed. "
            "Install httpx or run with BAND_MODE=mock."
        ) from exc

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, headers=headers, json=json)
        try:
            body = response.json()
        except Exception:  # noqa: BLE001
            body = {"_raw": response.text}
        return response.status_code, body
