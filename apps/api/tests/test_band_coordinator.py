"""Tests for the live Band coordinator config/build logic.

These never touch the network, the Band SDK, or any LLM. SDK construction is
exercised through injected fakes.
"""

import pytest

from band import coordinator
from core.config import Settings


def _live_settings(**overrides) -> Settings:
    base = dict(
        band_mode="sdk",
        band_agent_id="agent-123",
        band_api_key="band-secret",
        aiml_api_key="aiml-secret",
        aiml_default_model="gpt-4o",
        llm_provider="aiml",
        band_default_room_id="room-abc",
    )
    base.update(overrides)
    return Settings(**base)


def test_requires_sdk_mode() -> None:
    with pytest.raises(RuntimeError, match="BAND_MODE=sdk"):
        coordinator.build_coordinator_config(_live_settings(band_mode="mock"))


@pytest.mark.parametrize(
    "field, token",
    [
        ("band_agent_id", "BAND_AGENT_ID"),
        ("band_api_key", "BAND_API_KEY"),
    ],
)
def test_missing_credentials_named_clearly(field: str, token: str) -> None:
    with pytest.raises(RuntimeError, match=token):
        coordinator.build_coordinator_config(_live_settings(**{field: None}))


def test_missing_model_fails_with_aiml_hint() -> None:
    settings = _live_settings(aiml_default_model=None)
    with pytest.raises(RuntimeError, match="AIML_DEFAULT_MODEL"):
        coordinator.build_coordinator_config(settings)


def test_featherless_provider_is_disabled() -> None:
    with pytest.raises(RuntimeError, match="Featherless is disabled"):
        coordinator.build_coordinator_config(_live_settings(llm_provider="featherless"))


def test_aiml_provider_requires_key_and_model() -> None:
    with pytest.raises(RuntimeError, match="AIML_API_KEY"):
        coordinator.build_coordinator_config(
            _live_settings(llm_provider="aiml", aiml_api_key=None, aiml_default_model="gpt-4o")
        )
    with pytest.raises(RuntimeError, match="AIML_DEFAULT_MODEL"):
        coordinator.build_coordinator_config(
            _live_settings(llm_provider="aiml", aiml_api_key="aiml-secret", aiml_default_model=None)
        )


def test_aiml_provider_uses_aiml_endpoint() -> None:
    config = coordinator.build_coordinator_config(
        _live_settings(
            llm_provider="aiml",
            aiml_api_key="aiml-secret",
            aiml_default_model="gpt-4o",
        )
    )
    assert config.llm_provider == "aiml"
    assert config.llm_api_key == "aiml-secret"
    assert config.model == "gpt-4o"
    assert config.base_url == coordinator.DEFAULT_AIML_BASE_URL


def test_resolves_defaults_and_overrides() -> None:
    config = coordinator.build_coordinator_config(_live_settings())
    assert config.agent_id == "agent-123"
    assert config.llm_provider == "aiml"
    assert config.model == "gpt-4o"
    assert config.base_url == coordinator.DEFAULT_AIML_BASE_URL
    assert config.ws_url == coordinator.DEFAULT_THENVOI_WS_URL
    assert config.rest_url == coordinator.DEFAULT_THENVOI_REST_URL
    assert config.room_id == "room-abc"


def test_auto_provider_uses_aiml_and_endpoint_overrides() -> None:
    config = coordinator.build_coordinator_config(
        _live_settings(
            llm_provider="auto",
            thenvoi_ws_url="wss://custom/ws",
            thenvoi_rest_url="https://custom/",
        )
    )
    assert config.llm_provider == "aiml"
    assert config.model == "gpt-4o"
    assert config.ws_url == "wss://custom/ws"
    assert config.rest_url == "https://custom/"


def test_build_agent_wires_factories_without_network() -> None:
    calls: dict[str, dict] = {}

    def fake_chat_openai(**kwargs):
        calls["llm"] = kwargs
        return "LLM"

    def fake_adapter(**kwargs):
        calls["adapter"] = kwargs
        return "ADAPTER"

    def fake_saver():
        return "SAVER"

    class FakeAgent:
        @staticmethod
        def create(**kwargs):
            calls["agent"] = kwargs
            return "AGENT"

    config = coordinator.build_coordinator_config(_live_settings())
    result = coordinator.build_agent(
        config,
        chat_openai=fake_chat_openai,
        langgraph_adapter=fake_adapter,
        in_memory_saver=fake_saver,
        agent=FakeAgent,
    )

    assert result == "AGENT"
    assert calls["llm"] == {
        "model": "gpt-4o",
        "base_url": coordinator.DEFAULT_AIML_BASE_URL,
        "api_key": "aiml-secret",
    }
    assert calls["adapter"]["llm"] == "LLM"
    assert calls["adapter"]["checkpointer"] == "SAVER"
    assert calls["adapter"]["custom_section"] == coordinator.COORDINATOR_INSTRUCTIONS
    assert calls["agent"] == {
        "adapter": "ADAPTER",
        "agent_id": "agent-123",
        "api_key": "band-secret",
        "ws_url": coordinator.DEFAULT_THENVOI_WS_URL,
        "rest_url": coordinator.DEFAULT_THENVOI_REST_URL,
    }


def test_build_agent_accepts_specialist_instructions() -> None:
    calls: dict[str, dict] = {}

    def fake_adapter(**kwargs):
        calls["adapter"] = kwargs
        return "ADAPTER"

    class FakeAgent:
        @staticmethod
        def create(**kwargs):
            return "AGENT"

    coordinator.build_agent(
        coordinator.build_coordinator_config(_live_settings()),
        custom_section="SPECIALIST",
        chat_openai=lambda **kwargs: "LLM",
        langgraph_adapter=fake_adapter,
        in_memory_saver=lambda: "SAVER",
        agent=FakeAgent,
    )

    assert calls["adapter"]["custom_section"] == "SPECIALIST"
