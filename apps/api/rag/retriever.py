from typing import Any, Protocol


class ChunkSearchClient(Protocol):
    async def rpc(self, function_name: str, params: dict[str, Any]) -> list[dict[str, Any]]: ...


class Retriever:
    def __init__(self, client: ChunkSearchClient) -> None:
        self._client = client

    async def search(
        self,
        *,
        query_embedding: list[float],
        org_id: str,
        workflow_id: str,
        limit: int = 8,
        threshold: float = 0.2,
    ) -> list[dict[str, Any]]:
        if not org_id or not workflow_id:
            raise ValueError("org_id and workflow_id are required")
        return await self._client.rpc(
            "match_document_chunks",
            {
                "query_embedding": query_embedding,
                "match_org_id": org_id,
                "match_workflow_id": workflow_id,
                "match_threshold": threshold,
                "match_count": limit,
            },
        )

