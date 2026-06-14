# Multi-Agent LangGraph QA/RAG Architecture Using Band.ai + AIML API + Featherless

## Goal

Build a multi-agent QA/RAG system where:

- Band.ai provides collaborative rooms, peer discovery, agent mentions, and human-in-the-loop coordination.
- LangGraph provides deterministic stateful orchestration.
- AIML API provides OpenAI-compatible access to many hosted models.
- Featherless provides OpenAI-compatible access to open-weight models, embeddings, and tool-capable model families.

## Architecture

```text
User in Band room
  ↓ mentions @Coordinator
Band WebSocket event
  ↓
Remote Python process
  ↓
Band SDK Agent + LangGraphAdapter
  ↓
LangGraph QA graph
  ├── intent_router
  ├── ingestion_node
  ├── query_rewriter
  ├── retriever
  ├── reranker
  ├── answer_generator
  ├── judge
  └── band_response_node
  ↓
Band room response + trace events
```

## Agents

| Agent | Runtime | Responsibility |
|---|---|---|
| Coordinator | Band + LangGraph | Entry point, task routing, final response. |
| IngestionAgent | LangGraph node or separate Band agent | Parse documents, chunk, metadata, embeddings. |
| RetrieverAgent | LangGraph node/tool | Hybrid retrieval and evidence pack generation. |
| AnswerAgent | AIML/Featherless chat model | Generate answer from evidence. |
| JudgeAgent | AIML/Featherless reasoning model | Verify groundedness and answer quality. |
| OpsAgent | Tool/node | Metrics, traces, errors, progress events. |

## Provider split

| Task | Primary | Fallback |
|---|---|---|
| Final answer | AIML API strong chat model | Featherless strong open model |
| Judge | AIML reasoning model | Featherless Qwen/Kimi model |
| Embeddings | Featherless embedding model | AIML embedding model |
| Tool calling | Featherless Qwen/Kimi | AIML tool-capable model |
| Routing | cheap AIML/Featherless model | local rules |

## Database schema

```sql
CREATE TABLE rooms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  band_room_id TEXT UNIQUE NOT NULL,
  name TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  room_id UUID REFERENCES rooms(id),
  source_uri TEXT,
  title TEXT,
  content_hash TEXT,
  mime_type TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id),
  chunk_index INTEGER NOT NULL,
  text TEXT NOT NULL,
  token_count INTEGER,
  metadata JSONB DEFAULT '{}',
  content_hash TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chunk_id UUID REFERENCES chunks(id),
  provider TEXT NOT NULL,
  model TEXT NOT NULL,
  dimensions INTEGER,
  vector VECTOR,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(chunk_id, provider, model)
);

CREATE TABLE qa_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  room_id UUID REFERENCES rooms(id),
  band_message_id TEXT,
  question TEXT NOT NULL,
  final_answer TEXT,
  status TEXT DEFAULT 'started',
  provider_trace JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE qa_evidence (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  qa_run_id UUID REFERENCES qa_runs(id),
  chunk_id UUID REFERENCES chunks(id),
  score DOUBLE PRECISION,
  rank INTEGER,
  used_in_final BOOLEAN DEFAULT FALSE
);

CREATE TABLE qa_judgements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  qa_run_id UUID REFERENCES qa_runs(id),
  judge_provider TEXT,
  judge_model TEXT,
  faithfulness DOUBLE PRECISION,
  completeness DOUBLE PRECISION,
  citation_coverage DOUBLE PRECISION,
  risk TEXT,
  feedback TEXT,
  raw JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

## Chunking strategy

Use dynamic semantic chunking:

1. Parse document into structural blocks: heading, paragraph, table, code block, list, image caption.
2. Preserve hierarchy in metadata: section path, page number, heading path.
3. Merge small adjacent blocks until target token range.
4. Split oversized blocks by sentence/code/table row boundaries.
5. Add overlap only for prose, not tables/code.

Recommended defaults:

```yaml
chunking:
  target_tokens: 450
  min_tokens: 120
  max_tokens: 800
  overlap_tokens: 80
  split_priority:
    - heading_boundary
    - paragraph_boundary
    - sentence_boundary
    - token_boundary
```

## Metadata per chunk

```json
{
  "source_uri": "...",
  "document_title": "...",
  "mime_type": "application/pdf",
  "page_start": 4,
  "page_end": 5,
  "section_path": ["API", "Authentication"],
  "content_type": "prose|table|code|image_caption",
  "language": "en",
  "created_at_source": null,
  "version": null,
  "entities": ["Band", "LangGraph"],
  "keywords": ["websocket", "agent", "rest"]
}
```

## Retrieval strategy

Use staged retrieval:

```text
query rewrite
  → vector search top 30
  → keyword/BM25 top 30
  → metadata filters by room/project/source
  → merge/dedupe
  → rerank top 12
  → answer with top 6–8 evidence chunks
```

## Judge prompt contract

The judge must check only whether the answer is supported by evidence.

Output JSON:

```json
{
  "faithfulness": 0.0,
  "completeness": 0.0,
  "citation_coverage": 0.0,
  "unsupported_claims": [],
  "missing_evidence": [],
  "risk": "low|medium|high",
  "decision": "pass|revise|retrieve_more"
}
```

## One-day implementation order

1. Create a single Band remote agent: `@Coordinator`.
2. Connect it with `LangGraphAdapter`.
3. Create provider wrappers for AIML API and Featherless.
4. Add local Chroma or Postgres/pgvector.
5. Build ingestion for Markdown/text/PDF text first.
6. Build query → retrieve → answer graph.
7. Add judge node.
8. Add Band event traces.
9. Test in one Band room.

## Minimal files

```text
app/
  main.py
  config.py
  band_agent.py
  graph.py
  providers/
    aimlapi.py
    featherless.py
  rag/
    ingest.py
    chunk.py
    retrieve.py
    rerank.py
  db/
    schema.sql
    repository.py
  prompts/
    answer.md
    judge.md
```

## Provider wrapper interface

```python
from typing import Protocol, List

class ChatProvider(Protocol):
    async def ainvoke(self, messages: list[dict], **kwargs) -> str: ...

class EmbeddingProvider(Protocol):
    async def embed_documents(self, texts: List[str]) -> List[List[float]]: ...
    async def embed_query(self, text: str) -> List[float]: ...
```

## Final answer rule

The final answer should include:

- Direct answer first.
- Key evidence/citations.
- What is uncertain or missing.
- Next action if the user wants deeper work.

Never allow the answer node to invent facts not present in evidence for RAG questions.
