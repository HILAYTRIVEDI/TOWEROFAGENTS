# ATower Of Agents - Implementation Status

_Last assessed: 2026-06-18. Latest focused checks in this worktree: Python syntax check passed, `git diff --check` passed. Full `pytest` / frontend `tsc` were not run here because this worktree does not have its own `.venv` or `node_modules`._

The repo is still a deliberate bootstrap/scaffold: contracts, typed boundaries,
storage, catalog wiring, and UI shell are real, but product workflow execution
and indexing are not yet wired end to end.

## Implemented And Working

### Infrastructure / Scaffold
- Monorepo layout, `docker-compose.yml`, Dockerfiles for web + api, `.env.example`, and docs are present.
- FastAPI app has CORS, logging, health, routers, and local dev origins configured.
- Next.js app shell has dashboard, workflows, agents, Knowledge, docs, and reports areas.
- Favicon is wired through `/favicon.svg` and `/favicon.ico`.

### Agent And Band Setup
- API agent registry has 9 declared agents.
- Live Supabase agent catalog was checked and contains all 9 agent rows with Band handles:
  `workflow-router`, `rag-retriever`, `policy-guardian`, `final-decision`,
  `resume-jd-matcher`, `bias-reviewer`, `interview-planner`, `lead-qualifier`,
  and `engineering-reviewer`.
- Band remote-agent support exists via `band/coordinator.py` and `band/remote_agents.py`.
- Local `.env` in the main checkout had specialist Band credentials for the non-router agents; the Supabase catalog itself includes `@workflow-router`.

### Knowledge / Documents
- `POST /knowledge/{org_id}/documents` uploads organization-shared Knowledge documents to private Supabase Storage and inserts `documents.workflow_id = null`.
- `GET /knowledge/{org_id}/documents` now lists all org-scoped document rows, including shared Knowledge documents and workflow-specific files.
- `DELETE /knowledge/{org_id}/documents/{document_id}` removes an org-scoped document row and its private Storage object.
- Existing workflow upload remains available at `POST /workflows/{workflow_id}/documents`.
- The Knowledge page lists files, shows whether each row is `Shared knowledge` or `Workflow file`, and includes a Remove button.
- Upload validation still covers doc type, empty file, size cap, path-safe object names, content hash, and confidential-safe logging.

### RAG Primitives
- Parser, chunker, retriever contracts exist.
- Supabase vector search RPC exists.
- Retrieval design now expects workflow-specific chunks plus org-shared chunks.

### Workflow CRUD
- Workflow create/list/get/delete are Supabase-backed.
- Workflow detail can still upload workflow-specific artifacts.

## Pending / Not Yet Implemented

| Area | Remaining Work |
|---|---|
| Supabase migration | Apply `supabase/migrations/004_organization_documents.sql` to live Supabase. |
| Worktree dependencies | Create/install this worktree's `.venv` and `node_modules`; do not share mutable dependency folders between worktrees. |
| Full verification | Run `pnpm test:api`, `pnpm typecheck`, and `pnpm build` after dependencies are installed. |
| Document indexing | Parse uploaded docs, chunk them, generate embeddings, insert `document_chunks`, and update document status to `indexed` or `failed`. |
| Knowledge reuse in workflows | Workflow runs should retrieve both workflow-specific files and org Knowledge files without re-upload. |
| Embeddings provider | Replace mock/unconfigured embedding behavior with a real provider configured to `EMBEDDING_DIMENSIONS=1536`. |
| Workflow index endpoint | Replace `POST /workflows/{id}/index` `501` with real indexing orchestration. |
| Workflow run endpoint | Replace `POST /workflows/{id}/run` `501` with LangGraph execution. |
| Agent execution | Implement actual `run()` behavior for the HR screening agents first. |
| Findings and reports | Persist agent findings, generate workflow reports, and serve report endpoints. |
| Band workflow audit | Create/use Band rooms per workflow, add relevant participants, post progress/finding messages, and persist `band_messages`. |
| Auth/RLS | Replace temporary env org scope with Supabase auth-derived org scope and harden production RLS policies. |
| UI polish | Add Knowledge filters/search/date/size columns if needed, and clarify destructive delete behavior. |

## Explicitly Out Of Scope For Bootstrap

Per `AGENTS.md`: full RBAC, billing, production queues, OAuth integrations,
Slack/Teams, vendor crawling, complex analytics, perfect parsing, and a general
approval engine.

## Bottom Line

The control-plane foundation is in place: agents are cataloged, Band setup is
recognized, private document storage works, and the Knowledge dashboard can
upload/list/remove org-scoped files. The main remaining work is to apply the DB
migration, wire indexing and embeddings, then connect Knowledge retrieval into
the LangGraph HR Candidate Screening workflow with persisted findings, Band
audit messages, and reports.
