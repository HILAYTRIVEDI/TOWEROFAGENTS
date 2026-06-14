import logging
from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from core.config import Settings

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
        raise NotImplementedError("Live Band SDK integration is not implemented in the bootstrap")


def create_band_client(settings: Settings) -> BandClient:
    if settings.band_mode == "mock":
        return MockBandClient()
    if settings.band_mode == "sdk":
        return BandSDKClient(settings)
    raise ValueError(f"Unsupported BAND_MODE: {settings.band_mode}")

