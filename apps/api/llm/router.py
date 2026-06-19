from core.config import Settings
from llm.aiml_client import AIMLClient
from llm.base import ChatProvider, ChatResult


class MockChatProvider:
    async def complete(self, messages: list[dict[str, str]], model: str | None = None) -> ChatResult:
        return ChatResult(
            content="[mock] No external model was called.",
            provider="mock",
            model=model or "mock",
        )


class LLMRouter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def for_task(self, task: str) -> ChatProvider:
        provider = self._provider_name_for_task(task)
        if provider == "mock":
            return MockChatProvider()
        if provider == "aiml":
            if not self._settings.aiml_api_key:
                raise RuntimeError("AIML_API_KEY is not configured")
            return AIMLClient(
                self._settings.aiml_api_key,
                self._settings.aiml_default_model,
            )
        if provider == "featherless":
            raise RuntimeError(
                "Featherless is disabled for this deployment. Set LLM_PROVIDER=aiml "
                "and configure AIML_API_KEY/AIML_DEFAULT_MODEL."
            )
        raise ValueError(f"Unsupported LLM provider: {provider}")

    def _provider_name_for_task(self, task: str) -> str:
        if self._settings.llm_provider != "auto":
            return self._settings.llm_provider
        return "aiml"
