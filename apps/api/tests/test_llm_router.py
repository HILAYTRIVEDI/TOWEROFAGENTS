import pytest

from core.config import Settings
from llm.router import LLMRouter


@pytest.mark.asyncio
async def test_mock_router_never_calls_external_provider() -> None:
    provider = LLMRouter(Settings(llm_provider="mock")).for_task("synthesis")
    result = await provider.complete([{"role": "user", "content": "hello"}])
    assert result.provider == "mock"
    assert result.content.startswith("[mock]")


def test_auto_provider_uses_aiml(monkeypatch) -> None:
    captured = {}

    class FakeAIMLClient:
        def __init__(self, api_key: str, default_model: str | None) -> None:
            captured["api_key"] = api_key
            captured["default_model"] = default_model

    monkeypatch.setattr("llm.router.AIMLClient", FakeAIMLClient)

    provider = LLMRouter(
        Settings(
            llm_provider="auto",
            aiml_api_key="aiml-secret",
            aiml_default_model="aiml-model",
        )
    ).for_task("bias_review")

    assert isinstance(provider, FakeAIMLClient)
    assert captured == {"api_key": "aiml-secret", "default_model": "aiml-model"}


def test_featherless_provider_is_disabled() -> None:
    with pytest.raises(RuntimeError, match="Featherless is disabled"):
        LLMRouter(Settings(llm_provider="featherless")).for_task("synthesis")
