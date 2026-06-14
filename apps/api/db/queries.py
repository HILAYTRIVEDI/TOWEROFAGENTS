from typing import Any, Protocol


class QueryRepository(Protocol):
    async def save_agent_finding(self, finding: dict[str, Any]) -> dict[str, Any]: ...

    async def save_band_message(self, message: dict[str, Any]) -> dict[str, Any]: ...


class UnconfiguredRepository:
    async def save_agent_finding(self, finding: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("Supabase repository is not configured")

    async def save_band_message(self, message: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("Supabase repository is not configured")

