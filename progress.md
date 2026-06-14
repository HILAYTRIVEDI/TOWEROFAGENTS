# ATower Of Agents — Implementation Status

_Last assessed: 2026-06-14. Backend test suite: **32 passed**._

The repo is a **deliberate bootstrap/scaffold**: contracts, typed boundaries, and
infra are real and tested, but the actual product workflow (agent reasoning +
LangGraph execution) is intentionally stubbed with honest `NotImplementedError` /
`501` responses.

## ✅ Implemented & working

### Infrastructure / scaffold
- Monorepo layout (pnpm workspace, `docker-compose.yml`, Dockerfiles for web + api), `.env.example`, full docs set in `docs/`.
- FastAPI app (`main.py`) with CORS, logging, health, all routers wired.
- Pydantic schemas (`models/schemas.py`) and TS types (`apps/web/lib/types.ts`) as the shared contract.

### Document upload + RAG primitives (real)
- `routes/documents.py` → `db/documents.py`: real Supabase Storage upload + `documents` row insert, with org-scope resolution, path-traversal-safe object names, size/empty/type validation, sha256 hashing. Confidential-safe logging.
- `rag/parser.py` (txt/md/pdf/docx), `rag/chunker.py` (word-window + overlap), `rag/retriever.py` (pgvector `match_document_chunks` RPC wrapper). All real and tested.

### Band integration (real live path)
- `band/coordinator.py` + `band/remote_agents.py`: a genuine standalone process using the `thenvoi` SDK + LangGraph adapter over a Featherless model. Coordinator + specialist agents join rooms and reply to mentions. Honest config validation (clear errors when creds missing).
- `band/client.py`: in-process `MockBandClient` + explicitly-not-implemented `BandSDKClient`.

### LLM router
- `llm/router.py` routes tasks to AIML / Featherless / mock, raising explicit errors when keys are missing.

### Supabase
- Migrations `001_init`, `002_vector_search`, `003_documents_storage` + `seed.sql`.

### Workflow CRUD
- `routes/workflows.py`: create / list / get are real (Supabase-backed).

### Frontend
- Next.js app with dashboard, workflows (list/new/detail), agents, knowledge-base, reports pages; `lib/api.ts` fully wired to all backend endpoints; document-upload component + workflow-create form.

### Agent registry
- 9 agents declared with metadata + instruction prompts (`/agents` endpoint serves them).

## ❌ Remaining / stubbed (by design)

| Area | State |
|---|---|
| `workflows/executor.py` | `NotImplementedError` |
| `workflows/graph.py` (LangGraph) | `NotImplementedError` — node order planned only |
| All 9 agents | `ScaffoldAgent.run()` → `NotImplementedError` (only metadata/prompts exist) |
| `POST /workflows/{id}/run` & `/index` | `501 Not Implemented` |
| `GET /workflows/{id}/report` & `/reports/{id}` | `501` — no report persistence |
| Embeddings provider | `UnconfiguredEmbeddingProvider` raises — no real embedding model wired |
| In-process Band SDK posting | Not implemented (only the standalone coordinator process is live) |

## Explicitly out of scope (per AGENTS.md "Do Not Build Yet")
RBAC, billing, production queues, OAuth, Slack/Teams, vendor crawling, analytics, general approval engine.

## Bottom line
The "control plane" (upload → store → chunk/retrieve scaffolding, Band
collaboration, CRUD, dashboard) is built and tested. The **"brain"** — actual
agent execution, the LangGraph workflow, real embeddings, and report generation —
is the main remaining work, plus connecting indexing/retrieval into a runnable
end-to-end HR Candidate Screening flow.
