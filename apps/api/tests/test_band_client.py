import pytest
from core.config import Settings
from band.client import (
    MockBandClient,
    BandSDKClient,
    create_band_client,
    BandMessage,
)


@pytest.mark.asyncio
async def test_mock_band_client_operations() -> None:
    client = MockBandClient()
    # Create room
    room_id = await client.create_room("Test Room")
    assert room_id.startswith("mock-room-")

    # Post message
    msg = await client.post_message(room_id, "hello world")
    assert isinstance(msg, BandMessage)
    assert msg.room_id == room_id
    assert msg.content == "hello world"
    assert msg.mode == "mock"
    assert msg.id.startswith("mock-message-")


def test_band_sdk_client_unconfigured() -> None:
    # Missing credentials
    settings = Settings(
        band_mode="sdk",
        band_api_key=None,
        band_agent_id=None,
    )
    with pytest.raises(RuntimeError, match="Band credentials are not configured"):
        BandSDKClient(settings)


def test_band_sdk_client_configured_raises_not_implemented() -> None:
    # With credentials, it should raise NotImplementedError
    settings = Settings(
        band_mode="sdk",
        band_api_key="secret-key",
        band_agent_id="agent-123",
    )
    with pytest.raises(NotImplementedError, match="In-process Band SDK posting is not implemented"):
        BandSDKClient(settings)


def test_create_band_client_factory() -> None:
    # Test resolving "mock"
    settings_mock = Settings(band_mode="mock")
    client_mock = create_band_client(settings_mock)
    assert isinstance(client_mock, MockBandClient)

    # Test resolving "sdk"
    settings_sdk = Settings(
        band_mode="sdk",
        band_api_key="secret-key",
        band_agent_id="agent-123",
    )
    with pytest.raises(NotImplementedError):
        create_band_client(settings_sdk)

    # Test resolving invalid mode
    settings_invalid = Settings(band_mode="invalid")
    with pytest.raises(ValueError, match="Unsupported BAND_MODE: invalid"):
        create_band_client(settings_invalid)
