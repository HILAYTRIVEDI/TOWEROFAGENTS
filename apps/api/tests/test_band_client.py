import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from thenvoi_rest.agent_api_chats.types.create_agent_chat_response import (
    CreateAgentChatResponse,
)
from thenvoi_rest.agent_api_messages.types.create_agent_chat_message_response import (
    CreateAgentChatMessageResponse,
)
from thenvoi_rest.agent_api_participants.types.list_agent_chat_participants_response import (
    ListAgentChatParticipantsResponse,
)
from thenvoi_rest.types.chat_participant import ChatParticipant
from thenvoi_rest.types.chat_room import ChatRoom
from thenvoi_rest.types.message_sent_response import MessageSentResponse

from band.client import BandMessage, BandSDKClient, MockBandClient, create_band_client
from core.config import Settings


def test_mock_band_client() -> None:
    settings = Settings(band_mode="mock")
    client = create_band_client(settings)
    assert isinstance(client, MockBandClient)


@pytest.mark.asyncio
async def test_mock_band_client_methods() -> None:
    client = MockBandClient()
    room_id = await client.create_room("Test Room")
    assert room_id.startswith("mock-room-")

    msg = await client.post_message(room_id, "Hello world")
    assert isinstance(msg, BandMessage)
    assert msg.room_id == room_id
    assert msg.content == "Hello world"
    assert msg.mode == "mock"
    assert msg.id.startswith("mock-message-")


def test_sdk_client_initialization_fails_without_credentials() -> None:
    settings = Settings(band_mode="sdk", band_api_key=None, band_agent_id=None)
    with pytest.raises(RuntimeError, match="Band credentials are not configured"):
        create_band_client(settings)


def test_sdk_client_initialization_succeeds() -> None:
    settings = Settings(
        band_mode="sdk",
        band_api_key="key-123",
        band_agent_id="agent-123",
        thenvoi_rest_url="https://test.band.ai/",
    )
    client = create_band_client(settings)
    assert isinstance(client, BandSDKClient)
    assert client._client is not None


@pytest.mark.asyncio
async def test_sdk_client_create_room() -> None:
    settings = Settings(band_mode="sdk", band_api_key="key-123", band_agent_id="agent-123")
    client = create_band_client(settings)

    mock_chat_room = MagicMock(spec=ChatRoom)
    mock_chat_room.id = "room-999"
    mock_response = MagicMock(spec=CreateAgentChatResponse)
    mock_response.data = mock_chat_room

    client._client.agent_api_chats.create_agent_chat = AsyncMock(return_value=mock_response)

    room_id = await client.create_room("New Room")
    assert room_id == "room-999"
    client._client.agent_api_chats.create_agent_chat.assert_called_once()
    call_args = client._client.agent_api_chats.create_agent_chat.call_args[1]
    # Check title or task_id parameter in extra params
    assert call_args["chat"].title == "New Room"


@pytest.mark.asyncio
async def test_sdk_client_post_message_with_mentions() -> None:
    settings = Settings(band_mode="sdk", band_api_key="key-123", band_agent_id="agent-123")
    client = create_band_client(settings)

    env_overrides = {
        "BAND_WORKFLOW_ROUTER_AGENT_ID": "router-uuid",
    }

    mock_sent_response = MagicMock(spec=MessageSentResponse)
    mock_sent_response.id = "msg-uuid-111"
    mock_response = MagicMock(spec=CreateAgentChatMessageResponse)
    mock_response.data = mock_sent_response

    client._client.agent_api_messages.create_agent_chat_message = AsyncMock(
        return_value=mock_response
    )

    mock_participant = MagicMock(spec=ChatParticipant)
    mock_participant.handle = "dynamic-user"
    mock_participant.id = "user-uuid"

    mock_participants_response = MagicMock(spec=ListAgentChatParticipantsResponse)
    mock_participants_response.data = [mock_participant]
    client._client.agent_api_participants.list_agent_chat_participants = AsyncMock(
        return_value=mock_participants_response
    )

    with patch.dict(os.environ, env_overrides):
        msg = await client.post_message(
            "room-abc",
            "Hey @workflow-router and @dynamic-user, also non-existent @unknown",
        )

    assert msg.id == "msg-uuid-111"
    assert msg.room_id == "room-abc"
    assert msg.mode == "sdk"

    client._client.agent_api_messages.create_agent_chat_message.assert_called_once()
    call_args = client._client.agent_api_messages.create_agent_chat_message.call_args
    assert call_args[1]["chat_id"] == "room-abc"
    sent_message = call_args[1]["message"]

    mentions = sent_message.mentions
    assert len(mentions) == 2

    mentions_dict = {m.handle.lower(): m.id for m in mentions}
    assert mentions_dict["workflow-router"] == "router-uuid"
    assert mentions_dict["dynamic-user"] == "user-uuid"
    assert "unknown" not in mentions_dict


def test_create_band_client_factory_invalid() -> None:
    settings = Settings(band_mode="invalid")
    with pytest.raises(ValueError, match="Unsupported BAND_MODE: invalid"):
        create_band_client(settings)
