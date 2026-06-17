import logging
import os
import re
from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from core.config import Settings
from thenvoi.client.rest import (
    AsyncRestClient,
    ChatMessageRequest,
    ChatMessageRequestMentionsItem,
    ChatRoomRequest,
)

logger = logging.getLogger(__name__)


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


class BandSDKClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.band_api_key or not settings.band_agent_id:
            raise RuntimeError("Band credentials are not configured")
        self._settings = settings
        self._client = AsyncRestClient(
            api_key=settings.band_api_key,
            base_url=settings.thenvoi_rest_url or "https://app.band.ai/",
        )

    async def create_room(self, name: str) -> str:
        response = await self._client.agent_api_chats.create_agent_chat(
            chat=ChatRoomRequest(title=name)
        )
        return response.data.id

    async def post_message(self, room_id: str, content: str) -> BandMessage:
        # Build handle-to-ID mapping from settings and environment
        handle_to_id = {}
        if self._settings.band_agent_id:
            handle_to_id["coordinator"] = self._settings.band_agent_id
            handle_to_id["atower-coordinator"] = self._settings.band_agent_id
            handle_to_id["atowercoordinator"] = self._settings.band_agent_id

        from agents.registry import AGENT_TYPES
        for agent_type in AGENT_TYPES:
            slug = agent_type.slug
            prefix = f"BAND_{slug.replace('-', '_').upper()}"
            agent_id = os.environ.get(f"{prefix}_AGENT_ID", "").strip()
            if agent_id:
                handle_to_id[slug.lower()] = agent_id

        # Try dynamic lookup from room participants
        try:
            participants_resp = await self._client.agent_api_participants.list_agent_chat_participants(chat_id=room_id)
            if participants_resp and getattr(participants_resp, "data", None):
                for p in participants_resp.data:
                    if p.handle:
                        handle_to_id[p.handle.lower()] = p.id
        except Exception as e:
            logger.warning("Failed to fetch room participants dynamically: %s", e)

        # Parse mentions
        mention_handles = re.findall(r"@([\w-]+)", content)
        mentions = []
        for handle in mention_handles:
            h_lower = handle.lower()
            if h_lower in handle_to_id:
                mentions.append(
                    ChatMessageRequestMentionsItem(
                        id=handle_to_id[h_lower],
                        handle=handle,
                    )
                )

        response = await self._client.agent_api_messages.create_agent_chat_message(
            chat_id=room_id,
            message=ChatMessageRequest(
                content=content,
                mentions=mentions,
            ),
        )
        return BandMessage(
            id=response.data.id,
            room_id=room_id,
            content=content,
            mode="sdk",
        )


def create_band_client(settings: Settings) -> BandClient:
    if settings.band_mode == "mock":
        return MockBandClient()
    if settings.band_mode == "sdk":
        return BandSDKClient(settings)
    raise ValueError(f"Unsupported BAND_MODE: {settings.band_mode}")


