import pytest

from core.config import Settings
from llm.router import LLMRouter


@pytest.mark.asyncio
async def test_mock_router_never_calls_external_provider() -> None:
    provider = LLMRouter(Settings(llm_provider="mock")).for_task("synthesis")
    result = await provider.complete([{"role": "user", "content": "hello"}])
    assert result.provider == "mock"
    assert result.content.startswith("[mock]")

