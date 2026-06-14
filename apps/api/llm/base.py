from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ChatResult:
    content: str
    provider: str
    model: str


class ChatProvider(Protocol):
    async def complete(self, messages: list[dict[str, str]], model: str | None = None) -> ChatResult:
        ...

