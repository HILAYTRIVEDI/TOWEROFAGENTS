import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from uuid import uuid4

from core.config import Settings
from rag.parser import parse_document, ParsedDocument
from routes.workflows import index_workflow_documents


def test_parse_text_document() -> None:
    content = b"Hello world text content"
    parsed = parse_document("file.txt", content)
    assert isinstance(parsed, ParsedDocument)
    assert parsed.text == "Hello world text content"
    assert parsed.metadata == {"source": "file.txt"}


def test_parse_markdown_document() -> None:
    content = b"# Hello markdown"
    parsed = parse_document("doc.md", content)
    assert isinstance(parsed, ParsedDocument)
    assert parsed.text == "# Hello markdown"
    assert parsed.metadata == {"source": "doc.md"}


def test_parse_unsupported_document() -> None:
    with pytest.raises(ValueError, match="Unsupported document type: .pdfx"):
        parse_document("doc.pdfx", b"binary content")


@patch("pypdf.PdfReader")
def test_parse_pdf_document(mock_pdf_reader) -> None:
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1 content"
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page 2 content"

    mock_reader_instance = MagicMock()
    mock_reader_instance.pages = [mock_page1, mock_page2]
    mock_pdf_reader.return_value = mock_reader_instance

    content = b"fake pdf binary"
    parsed = parse_document("doc.pdf", content)

    mock_pdf_reader.assert_called_once()
    assert parsed.text == "Page 1 content\n\nPage 2 content"
    assert parsed.metadata == {"source": "doc.pdf"}


@patch("docx.Document")
def test_parse_docx_document(mock_docx_document) -> None:
    p1 = MagicMock()
    p1.text = "Paragraph 1 content"
    p2 = MagicMock()
    p2.text = "Paragraph 2 content"

    mock_doc_instance = MagicMock()
    mock_doc_instance.paragraphs = [p1, p2]
    mock_docx_document.return_value = mock_doc_instance

    content = b"fake docx binary"
    parsed = parse_document("doc.docx", content)

    mock_docx_document.assert_called_once()
    assert parsed.text == "Paragraph 1 content\nParagraph 2 content"
    assert parsed.metadata == {"source": "doc.docx"}


@pytest.mark.asyncio
async def test_index_workflow_documents_unsupported_type_fails() -> None:
    workflow_id = uuid4()
    org_id = uuid4()
    doc_id = uuid4()
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-key",
        embedding_provider="mock",
    )

    # Spy tables to track updates
    workflow_updates = []
    document_updates = []

    class SpyTable:
        def __init__(self, table_name, data=None):
            self.table_name = table_name
            self.data = data or []

        def select(self, *args, **kwargs):
            return self

        def eq(self, *args, **kwargs):
            return self

        def limit(self, *args, **kwargs):
            return self

        def delete(self, *args, **kwargs):
            return self

        def insert(self, *args, **kwargs):
            return self

        def update(self, data):
            if self.table_name == "workflows":
                workflow_updates.append(data)
            elif self.table_name == "documents":
                document_updates.append(data)
            return self

        def execute(self):
            resp = MagicMock()
            resp.data = self.data
            return resp

    class MockSupabaseClientSpy:
        def __init__(self):
            self.storage = MagicMock()
            self.storage.from_.return_value.download.return_value = b"Unsupported type bytes"

        def table(self, table_name):
            if table_name == "workflows":
                return SpyTable("workflows", [{"id": str(workflow_id), "org_id": str(org_id)}])
            elif table_name == "documents":
                return SpyTable("documents", [{
                    "id": str(doc_id),
                    "filename": "document.xyz",  # xyz is unsupported
                    "storage_path": f"{workflow_id}/document.xyz",
                    "org_id": str(org_id),
                }])
            return SpyTable(table_name)

    mock_client = MockSupabaseClientSpy()

    with patch("routes.workflows.create_supabase_client", return_value=mock_client):
        await index_workflow_documents(workflow_id, settings)

        # The document update should have moved to "failed"
        assert any(update.get("status") == "failed" for update in document_updates)
        # The workflow update should have moved to "failed"
        assert any(update.get("status") == "failed" for update in workflow_updates)
