from typing import Any

import pytest

from rag.retriever import Retriever


class FakeSearchClient:
    def __init__(self) -> None:
        self.params: dict[str, Any] | None = None

    async def rpc(self, function_name: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        assert function_name == "match_document_chunks"
        self.params = params
        return [{"id": "chunk-1"}]


@pytest.mark.asyncio
async def test_retriever_scopes_search_to_org_and_workflow() -> None:
    client = FakeSearchClient()
    results = await Retriever(client, dimensions=2).search(
        query_embedding=[0.1, 0.2],
        org_id="org-1",
        workflow_id="workflow-1",
    )
    assert results == [{"id": "chunk-1"}]
    assert client.params is not None
    assert client.params["match_org_id"] == "org-1"
    assert client.params["match_workflow_id"] == "workflow-1"


@pytest.mark.asyncio
async def test_retriever_rejects_query_embedding_dimension_mismatch() -> None:
    client = FakeSearchClient()

    with pytest.raises(RuntimeError, match="expected 3"):
        await Retriever(client, dimensions=3).search(
            query_embedding=[0.1, 0.2],
            org_id="org-1",
            workflow_id="workflow-1",
        )

    assert client.params is None
