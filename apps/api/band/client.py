"""Band client abstractions (room creation / generic message posting).

For conversational @mention posting during workflow runs, see
band.run_audit.WorkflowRoomAuditor — it handles the per-specialist mention
chain and honest mock/real/failed mode tracking.
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Protocol
from uuid import uuid4

from core.config import Settings

logger = logging.getLogger(__name__)

# Band REST base default — mirrors coordinator.py DEFAULT_THENVOI_REST_URL.
_DEFAULT_REST_URL = "https://app.band.ai"


@dataclass(frozen=True)
class BandMessage:
    id: str
    room_id: str
    content: str
    mode: str


class BandClient(Protocol):
    async def create_room(self, name: str) -> str: ...

    async def post_message(self, room_id: str, content: str) -> BandMessage: ...


class MockBandClient:
    async def create_room(self, name: str) -> str:
        room_id = f"mock-room-{uuid4()}"
        logger.info("[mock-band] created room %s (%s)", room_id, name)
        return room_id

    async def post_message(self, room_id: str, content: str) -> BandMessage:
        message = BandMessage(
            id=f"mock-message-{uuid4()}",
            room_id=room_id,
            content=content,
            mode="mock",
        )
        logger.info("[mock-band] %s: %s", room_id, content)
        return message


async def _default_http_post(url: str, *, headers: dict, json: dict) -> tuple[int, dict]:
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


class BandSDKClient:
    """In-process Band REST client for room creation and generic message posting.

    Uses Band's Agent REST API directly (X-API-Key auth, coordinator credentials).
    http_post is injectable for testing without network:
        async def http_post(url, *, headers, json) -> (status_code, body_dict)

    The room creation endpoint (POST /api/v1/agent/chats) is inferred from the
    Band Agent API naming convention established in run_audit.py and band_ai_docs.md.
    It cannot be verified without live credentials — canary: the endpoint and
    response shape must be confirmed against Band's live API when keys are available.
    """

    def __init__(
        self,
        settings: Settings,
        http_post: Callable[..., Coroutine[Any, Any, tuple[int, dict]]] | None = None,
    ) -> None:
        if not settings.band_api_key or not settings.band_agent_id:
            raise RuntimeError(
                "Band SDK is not configured: BAND_API_KEY and BAND_AGENT_ID must be set."
            )
        self._api_key: str = settings.band_api_key
        self._rest_base = (settings.thenvoi_rest_url or _DEFAULT_REST_URL).rstrip("/")
        self._http_post = http_post or _default_http_post

    async def create_room(self, name: str) -> str:
        # ponytail: endpoint is POST /api/v1/agent/chats, inferred from the
        # Band Agent API path used in run_audit.py (/api/v1/agent/chats/{id}/messages).
        # Response shape {"data": {"id": "..."}} follows the same convention.
        # Both must be verified against live Band API when credentials are available.
        url = f"{self._rest_base}/api/v1/agent/chats"
        headers = {"X-API-Key": self._api_key, "Content-Type": "application/json"}
        body = {"name": name}
        status_code, data = await self._http_post(url, headers=headers, json=body)
        if status_code < 200 or status_code >= 300:
            raise RuntimeError(
                f"[sdk-band] create_room returned HTTP {status_code}: {data}"
            )
        room_id = (data.get("data") or {}).get("id")
        if not room_id:
            raise RuntimeError(f"[sdk-band] create_room: no room id in response: {data}")
        logger.info("[sdk-band] created room %s (%s)", room_id, name)
        return str(room_id)

    async def post_message(self, room_id: str, content: str) -> BandMessage:
        url = f"{self._rest_base}/api/v1/agent/chats/{room_id}/messages"
        headers = {"X-API-Key": self._api_key, "Content-Type": "application/json"}
        body = {"message": {"content": content, "mentions": []}}
        status_code, data = await self._http_post(url, headers=headers, json=body)
        if status_code < 200 or status_code >= 300:
            raise RuntimeError(
                f"[sdk-band] post_message returned HTTP {status_code}: {data}"
            )
        band_id = (data.get("data") or {}).get("id") or f"sdk-message-{uuid4()}"
        return BandMessage(id=str(band_id), room_id=room_id, content=content, mode="real")


def create_band_client(settings: Settings) -> BandClient:
    if settings.band_mode == "mock":
        return MockBandClient()
    if settings.band_mode == "sdk":
        return BandSDKClient(settings)
    raise ValueError(f"Unsupported BAND_MODE: {settings.band_mode}")

