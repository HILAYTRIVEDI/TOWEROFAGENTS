from openai import AsyncOpenAI

from llm.base import ChatResult


class FeatherlessClient:
    def __init__(self, api_key: str, default_model: str | None) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url="https://api.featherless.ai/v1")
        self._default_model = default_model

    async def complete(self, messages: list[dict[str, str]], model: str | None = None) -> ChatResult:
        selected_model = model or self._default_model
        if not selected_model:
            raise RuntimeError("FEATHERLESS_DEFAULT_MODEL is not configured")
        response = await self._client.chat.completions.create(
            model=selected_model,
            messages=messages,  # type: ignore[arg-type]
        )
        return ChatResult(
            content=response.choices[0].message.content or "",
            provider="featherless",
            model=selected_model,
        )

