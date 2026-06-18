# ATower Of Agents - Implementation Status

_Last assessed: 2026-06-19. `pytest apps/api/tests` → 87 passed. The HR candidate-screening workflow was driven end-to-end through the running stack (FastAPI :8000 + Next.js :3000) against live Supabase with the real AIML LLM provider (embeddings still mock): create workflow → upload resume/JD/policy → index → run → view decision packet at `/reports/{id}`. Confirmed non-mock output (`any_mock: False`, 5 specialist agents ran, 6 chunks retrieved)._

The HR candidate-screening workflow now executes end to end. Specialist agents
run behind the typed LLM provider interface and synthesize a persisted,
human-review-gated decision packet rendered in the web UI. Remaining gaps are
real embeddings, LangGraph orchestration, and Band audit messaging.

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
- Uploaded workflow and Knowledge documents schedule background ingestion.
- `POST /workflows/{id}/index` re-indexes every workflow-attached document.

### Workflow CRUD
- Workflow create/list/get/delete are Supabase-backed.
- Workflow detail can still upload workflow-specific artifacts.

### Workflow Reports (HR candidate screening — end to end)
- `POST /workflows/{id}/run` executes the HR specialist agents (`specialist_agents_v1`):
  resume-jd-matcher, bias-reviewer, interview-planner, policy-guardian, and
  final-decision synthesis. It persists a decision packet and moves the workflow
  to `awaiting_review`. (`workflow-router` and `rag-retriever` are declared but
  not yet implemented and are recorded as skipped, not faked.)
- Each agent runs behind the typed `ChatProvider` interface via `LLMRouter`. With
  a real provider (AIML) the findings are genuine; with the `mock` provider every
  finding is explicitly flagged `[PLACEHOLDER]`, `confidence=0.0`, and forces
  `requires_human_review`. `any_mock` is recorded in the report payload.
- The decision packet carries recommendation, summary, strengths, gaps,
  LLM-generated interview questions, policy note, and evidence chunk IDs collected
  only from actually-retrieved context. `fit_score` is never fabricated (stays
  null unless an agent is explicitly designed to emit one).
- MVP human-in-the-loop: `requires_human_review` is always True until a formal
  approval step is wired in.
- `GET /workflows/{id}/report` and `GET /reports/{report_id}` read persisted reports.
- Workflow runs retrieve relevant chunks from workflow-specific documents and
  organization-shared Knowledge documents when embeddings are configured.
- Web UI: `RunWorkflow` component (re-index + run) on the workflow detail page;
  full decision-packet view at `/reports/{report_id}` with a human-review banner.

## Pending / Not Yet Implemented

| Area | Remaining Work |
|---|---|
| Supabase migration | Apply `supabase/migrations/004_organization_documents.sql` to live Supabase. |
| Worktree dependencies | Create/install this worktree's `.venv` and `node_modules`; do not share mutable dependency folders between worktrees. |
| Full verification | Run `pnpm test:api`, `pnpm typecheck`, and `pnpm build` after dependencies are installed. |
| Embeddings provider | Replace mock embedding behavior with a real provider configured to `EMBEDDING_DIMENSIONS=1536`. (LLM provider is real AIML; embeddings are still mock.) |
| LangGraph orchestration | The executor runs specialist agents sequentially; port to a LangGraph graph for branching/router-driven flows. |
| Remaining agents | Implement `run()` for `workflow-router` and `rag-retriever` (currently recorded as skipped). HR screening agents are implemented. |
| Provider name in payload | `providers_used` logs `"unknown"` because the provider object doesn't expose a name; `any_mock` is authoritative. Surface the real provider/model name. |
| Band workflow audit | Create/use Band rooms per workflow, add relevant participants, post progress/finding messages, and persist `band_messages`. |
| Auth/RLS | Replace temporary env org scope with Supabase auth-derived org scope and harden production RLS policies. |
| UI polish | Add Knowledge filters/search/date/size columns if needed, and clarify destructive delete behavior. |

## Explicitly Out Of Scope For Bootstrap

Per `AGENTS.md`: full RBAC, billing, production queues, OAuth integrations,
Slack/Teams, vendor crawling, complex analytics, perfect parsing, and a general
approval engine.

## Bottom Line

The HR Candidate Screening workflow runs end to end through the web UI: agents
are cataloged, private document storage and indexing work, and a run drives five
specialist agents behind the typed LLM interface to a persisted, human-review-gated
decision packet shown at `/reports/{id}` — verified against live Supabase with the
real AIML provider. The main remaining work is real embeddings, LangGraph
orchestration, the two unimplemented agents (`workflow-router`, `rag-retriever`),
and Band audit messaging.
