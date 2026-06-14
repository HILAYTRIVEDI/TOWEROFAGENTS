# RAG Design

## Pipeline

```text
Storage upload -> parser -> structure-aware chunker -> embeddings
-> document_chunks -> match_document_chunks retrieval
```

Supported MVP formats will be PDF (`pypdf`), DOCX (`python-docx`), Markdown, and text. CSV is optional.

Chunks target 700-1000 tokens with 100-150 token overlap when structural boundaries are unavailable. Metadata includes document type, source, section, page, workflow, access scope, and confidentiality.

Retrieval must filter by `org_id` and `workflow_id`. The base scaffold defines parser/chunker/retriever contracts only; it does not generate embeddings or access Supabase.

