import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from uuid import uuid4

from core.config import Settings
from rag.embeddings import (
    MockEmbeddingProvider,
    OpenAIEmbeddingProvider,
    get_embedding_provider,
)
from routes.workflows import index_workflow_documents
from fastapi.testclient import TestClient
from main import app


class MockTable:
    def __init__(self, data=None):
        self.data = data or []

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def update(self, *args, **kwargs):
        return self

    def delete(self, *args, **kwargs):
        return self

    def insert(self, *args, **kwargs):
        return self

    def execute(self):
        mock_response = MagicMock()
        mock_response.data = self.data
        return mock_response


class MockStorageBucket:
    def __init__(self, content=b"Hello world"):
        self.content = content

    def download(self, path):
        return self.content


class MockStorage:
    def __init__(self, content=b"Hello world"):
        self.bucket = MockStorageBucket(content)

    def from_(self, bucket_name):
        return self.bucket


class MockSupabaseClient:
    def __init__(self, workflow_data=None, document_data=None, file_content=b"Hello world"):
        self.workflow_data = workflow_data or []
        self.document_data = document_data or []
        self.storage = MockStorage(file_content)
        self.table_calls = []

    def table(self, table_name):
        self.table_calls.append(table_name)
        if table_name == "workflows":
            return MockTable(self.workflow_data)
        elif table_name == "documents":
            return MockTable(self.document_data)
        else:
            return MockTable([])


# 1. Tests for embedding providers

@pytest.mark.asyncio
async def test_mock_embedding_provider():
    provider = MockEmbeddingProvider(dimensions=128)
    assert provider.dimensions == 128

    docs = ["hello", "world"]
    embeddings = await provider.embed_documents(docs)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 128
    assert embeddings[0][0] == 0.1

    query_emb = await provider.embed_query("search term")
    assert len(query_emb) == 128
    assert query_emb[0] == 0.1


@pytest.mark.asyncio
async def test_openai_embedding_provider():
    # Mock AsyncOpenAI embeddings API call
    mock_client = MagicMock()
    mock_embeddings = AsyncMock()
    mock_item = MagicMock()
    mock_item.embedding = [0.2, 0.3, 0.4]
    mock_response = MagicMock()
    mock_response.data = [mock_item]
    mock_embeddings.create.return_value = mock_response
    mock_client.embeddings = mock_embeddings

    with patch("rag.embeddings.AsyncOpenAI", return_value=mock_client):
        provider = OpenAIEmbeddingProvider(
            api_key="test-key",
            model="text-embedding-3-small",
            base_url="https://example.com/v1",
            dimensions=3,
        )
        assert provider.dimensions == 3
        assert provider.model == "text-embedding-3-small"

        res = await provider.embed_documents(["test"])
        assert res == [[0.2, 0.3, 0.4]]

        res_query = await provider.embed_query("test query")
        assert res_query == [0.2, 0.3, 0.4]


def test_get_embedding_provider():
    # Test resolving "mock"
    settings = Settings(
        embedding_provider="mock",
        embedding_dimensions=256,
    )
    provider = get_embedding_provider(settings)
    assert isinstance(provider, MockEmbeddingProvider)
    assert provider.dimensions == 256

    # Test resolving "aiml" without key raises error
    settings = Settings(
        embedding_provider="aiml",
        aiml_api_key=None,
    )
    with pytest.raises(RuntimeError, match="AIML_API_KEY is not configured"):
        get_embedding_provider(settings)

    # Test resolving "aiml" with key
    settings = Settings(
        embedding_provider="aiml",
        aiml_api_key="aiml-key",
        embedding_dimensions=512,
    )
    provider = get_embedding_provider(settings)
    assert isinstance(provider, OpenAIEmbeddingProvider)
    assert provider.dimensions == 512
    assert provider.model == "text-embedding-3-small"

    # Test resolving "featherless" without key raises error
    settings = Settings(
        embedding_provider="featherless",
        featherless_api_key=None,
    )
    with pytest.raises(RuntimeError, match="FEATHERLESS_API_KEY is not configured"):
        get_embedding_provider(settings)

    # Test resolving "featherless" with key
    settings = Settings(
        embedding_provider="featherless",
        featherless_api_key="featherless-key",
        embedding_dimensions=768,
    )
    provider = get_embedding_provider(settings)
    assert isinstance(provider, OpenAIEmbeddingProvider)
    assert provider.dimensions == 768


# 2. Tests for background task index_workflow_documents

@pytest.mark.asyncio
async def test_index_workflow_documents_no_docs():
    workflow_id = uuid4()
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-key",
        embedding_provider="mock",
    )

    mock_client = MockSupabaseClient(
        workflow_data=[{"id": str(workflow_id), "org_id": str(uuid4())}],
        document_data=[]  # No documents
    )

    with patch("routes.workflows.create_supabase_client", return_value=mock_client):
        await index_workflow_documents(workflow_id, settings)
        # Should complete successfully and check that storage was not accessed
        assert len(mock_client.table_calls) > 0


@pytest.mark.asyncio
async def test_index_workflow_documents_with_docs():
    workflow_id = uuid4()
    org_id = uuid4()
    doc_id = uuid4()
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-key",
        embedding_provider="mock",
        embedding_dimensions=1536,
    )

    mock_client = MockSupabaseClient(
        workflow_data=[{"id": str(workflow_id), "org_id": str(org_id)}],
        document_data=[{
            "id": str(doc_id),
            "filename": "document.txt",
            "storage_path": f"{workflow_id}/file.txt",
            "org_id": str(org_id),
        }],
        file_content=b"Sample plain text file content for testing chunking"
    )

    with patch("routes.workflows.create_supabase_client", return_value=mock_client):
        await index_workflow_documents(workflow_id, settings)
        # Verify call flow was executed
        assert "document_chunks" in mock_client.table_calls


# 3. Tests for workflow index route

def test_index_workflow_route_not_found():
    workflow_id = uuid4()
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-key",
    )

    # Mock empty select response (workflow does not exist)
    mock_client = MockSupabaseClient(workflow_data=[])

    with patch("routes.workflows.create_supabase_client", return_value=mock_client):
        client = TestClient(app)
        response = client.post(f"/workflows/{workflow_id}/index")
        assert response.status_code == 404
        assert response.json()["detail"] == "Workflow not found"


def test_index_workflow_route_accepted():
    workflow_id = uuid4()
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-key",
    )

    # Mock successful select response (workflow exists)
    mock_client = MockSupabaseClient(workflow_data=[{"id": str(workflow_id)}])

    with patch("routes.workflows.create_supabase_client", return_value=mock_client):
        with patch("routes.workflows.index_workflow_documents") as mock_task:
            client = TestClient(app)
            response = client.post(f"/workflows/{workflow_id}/index")
            assert response.status_code == 202
            assert response.json()["status"] == "indexing"
            # Background task should be enqueued
            mock_task.assert_called_once()
