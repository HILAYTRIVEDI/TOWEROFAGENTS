# ATower Of Agents - Implementation Status

_Last assessed: 2026-06-27. Workflow discussion/audit trail and decision reasoning are now surfaced inline on `/workflows/{id}`. `.venv/bin/python -m pytest apps/api/tests` passed with 103 tests; `npm run typecheck` and `npm run build` in `apps/web` passed. The web build still reports an existing `app/page.tsx` hook dependency warning. Backend Band workflow-audit path is wired and covered by focused tests. LLM routing and the Band coordinator use AIML API only; Featherless is disabled for this deployment._

## Current Plan: Workflow Discussion, Audit, And Decision Trail

Source plan: `/Users/hilaytrivedi/.codex/attachments/1858fe33-a67c-42ef-8526-b36adf83076e/pasted-text.txt`.

- [x] Add repository methods to persist `agent_findings` and read `band_messages` / `agent_findings`.
- [x] Persist full per-agent findings from `POST /workflows/{id}/run` without failing the run on persistence errors.
- [x] Add `GET /workflows/{id}/messages` and `GET /workflows/{id}/findings` response contracts.
- [x] Add frontend types and API helpers for messages and findings.
- [x] Render inline `Agent discussion & audit trail` and `Decision & reasoning` sections on `/workflows/{id}`.
- [x] Label placeholder/mock data explicitly using report `any_mock`, message `raw_payload.mode`, and zero-confidence findings.
- [x] Document the new API contracts and real embedding provider configuration path in `.env.example`.
- [x] Run focused backend tests (`.venv/bin/python -m pytest apps/api/tests/test_workflows.py` -> 14 passed).
- [x] Run full backend tests (`.venv/bin/python -m pytest apps/api/tests` -> 103 passed).
- [x] Run frontend type/build checks (`npm run typecheck` and `npm run build` in `apps/web` passed; build still reports an existing `app/page.tsx` hook dependency warning).
- [x] Polish workflow-page rendering after visual review: mock Band audit rows no longer mark the decision as placeholder, long LLM text is wrapped/cleaned, and the mock-session button is hidden once a room is assigned.
- [x] Fix backend report summary generation: final-decision text is no longer truncated at 300 characters, and skipped/not-implemented wording appears only when agents actually skip.
- [x] Add workflow artifact history: `GET /workflows/{id}/documents` hydrates the workflow Documents card, and the UI shows uploaded files under document-type tabs.
- [x] Add scoped workflow artifact removal: `DELETE /workflows/{id}/documents/{document_id}` deletes the matching workflow file/storage object, and the workflow Documents card now shows Remove actions.
- [x] Ensure HR agents receive resume and job-description context: workflow runs now perform broad + resume-targeted + JD-targeted retrieval queries, dedupe chunks, and label chunk metadata with document type/filename for the Resume/JD matcher.
- [x] Wire LangGraph orchestration: `build_workflow_graph()` builds/compiles a `StateGraph` (one node per selected agent in template order + terminal aggregate-report node), `WorkflowExecutor.run()` is now a thin driver that `ainvoke`s the compiled graph, and per-node dispatch lives in `workflows/agent_nodes.py`. Sequential `for` loop removed; ScaffoldAgent `NotImplementedError` still lands in `skipped_slugs`; return shape and report payload unchanged. Verified: `.venv/bin/python -m pytest apps/api` -> 117 passed (111 prior + 6 new parity tests in `tests/test_graph_parity.py`).
- [x] Add human approval API: `POST /workflows/{id}/review` accepts `{decision: approve|reject, note?}`, transitions a persisted `review_status` (`pending_review` -> `approved`|`rejected`), and stores reviewer note + `reviewed_at`. New migration `supabase/migrations/005_report_review_status.sql` adds the columns (apply to live Supabase manually — does not auto-apply). `WorkflowReportRead` now surfaces `review_status`/`reviewer_note`/`reviewed_at`; new `ReviewStatus` enum + `WorkflowReviewRequest`/`WorkflowReviewRead` models. Invalid transitions rejected: 404 (no report), 400 (report doesn't require review), 409 (already resolved). `requires_human_review` stays the trigger, `review_status` is the single-source-of-truth resolution. Verified: `.venv/bin/python -m pytest apps/api` -> 122 passed (5 new review tests).
- [x] Build approval UI (Part F2): new `ReviewStatus` union + `WorkflowReviewRead` type and three nullable review fields on `WorkflowReport` (`apps/web/lib/types.ts`); `submitReview(workflowId, decision, note?)` helper (`apps/web/lib/api.ts`); new `ReportReviewPanel` client island (`apps/web/components/report-review-panel.tsx`) with Approve/Reject + optional note, rendered on `reports/[id]` and hiding actions once resolved; `review_status` badge on `workflows/[id]`; badge styles in `globals.css`. 4xx handled (404/400 surface backend `detail`; 409 prompts refresh). Verified: `npm run typecheck` pass, `npm run build` pass (only the pre-existing `app/page.tsx` hook warning).
- [x] Automatic Band room creation (Part C): `BandSDKClient` (`apps/api/band/client.py`) now implements `create_room()` (`POST /api/v1/agent/chats`) and `post_message()` against Band's Agent REST API via injectable httpx `http_post`, mirroring `MockBandClient` and the `run_audit.py` call pattern (async httpx, `X-API-Key`, `data.id` parsing). `/band-session` now provisions a real room when `BAND_MODE=sdk` + creds present; returns HTTP 503 unconfigured (names both missing env vars) when sdk creds absent; HTTP 400 for unknown modes; mock branch unchanged. Docs updated (`docs/BAND_INTEGRATION.md`). Verified: `python -m pytest apps/api/tests -q` -> 122 passed. **Unverifiable without live keys:** real room creation HTTP call, and the `create_room` request body field name (Band returned 422 "Unexpected field: name" with live creds — flagged in a code comment at `client.py:98`; confirm the correct field against Band's live API once keys exist).
- [ ] Real embeddings end-to-end (Part D): wire real embedding provider behind `rag/embeddings.py`, ensure index/retrieve dimensional parity, keep mock fallback.
- [ ] Perform live mock baseline and real-provider verification after keys are configured.

## Implemented And Working

### Infrastructure / Scaffold
- Monorepo layout, `docker-compose.yml`, Dockerfiles for web + api, `.env.example`, and docs are present.
- FastAPI app has CORS, logging, health, routers, and local dev origins configured.
- Next.js app shell has dashboard, workflows, agents, Knowledge, docs, and reports areas.
- Favicon is wired through `/favicon.svg` and `/favicon.ico`.

### Agent And Band Setup
- API agent registry has 9 declared agents.
- Live Supabase agent catalog was previously checked and contains all 9 agent rows with Band handles:
  `workflow-router`, `rag-retriever`, `policy-guardian`, `final-decision`,
  `resume-jd-matcher`, `bias-reviewer`, `interview-planner`, `lead-qualifier`,
  and `engineering-reviewer`.
- Band remote-agent support exists via `band/coordinator.py` and `band/remote_agents.py`.
- Workflow-run Band audit support exists via `band/run_audit.py`; `/workflows/{id}/run`
  posts one message per executed specialist and persists `band_messages` when a
  room/default room is configured. In `BAND_MODE=mock`, messages are persisted as
  mock with no network call.

### Knowledge / Documents
- Organization-shared Knowledge documents can be uploaded, listed, deleted, and used alongside workflow-specific files.
- Existing workflow upload remains available at `POST /workflows/{workflow_id}/documents`.
- Upload validation covers doc type, empty file, size cap, path-safe object names, content hash, and confidential-safe logging.

### RAG Primitives
- Parser, chunker, retriever contracts exist.
- Supabase vector search RPC exists.
- Retrieval design expects workflow-specific chunks plus org-shared chunks.
- Uploaded workflow and Knowledge documents schedule background ingestion.
- `POST /workflows/{id}/index` re-indexes every workflow-attached document.

### Workflow CRUD
- Workflow create/list/get/delete are Supabase-backed.
- Workflow detail can upload workflow-specific artifacts.
- Workflows can be assigned a separate Band discussion room/session at creation
  or from the workflow detail page.

### Workflow Reports (HR candidate screening)
- `POST /workflows/{id}/run` executes the HR specialist agents (orchestrated by a compiled LangGraph `StateGraph`) and persists a decision packet.
- Each agent runs behind the typed `ChatProvider` interface via `LLMRouter`.
- Mock provider outputs are explicitly flagged `[PLACEHOLDER]`, `confidence=0.0`, and force human review.
- The decision packet carries recommendation, summary, strengths, gaps, interview questions, policy note, and evidence chunk IDs from retrieved context.
- MVP human-in-the-loop: `requires_human_review` is always true until a formal approval step is wired in.
- `GET /workflows/{id}/report` and `GET /reports/{report_id}` read persisted reports.

## Pending / Not Yet Implemented

| Area | Remaining Work |
|---|---|
| Live mock/real demo | Run the new inline workflow page against a mock baseline and then real provider keys. |
| Supabase migration | Apply `supabase/migrations/004_organization_documents.sql` to live Supabase if not already applied. |
| Worktree dependencies | Create/install this worktree's `.venv` and `node_modules`; do not share mutable dependency folders between worktrees. |
| Embeddings provider | Configure a real embedding provider with `EMBEDDING_PROVIDER=aiml` or `openai`, `EMBEDDING_MODEL`, and `EMBEDDING_DIMENSIONS=1536`. |
| Band room provisioning | Create real Band rooms and add relevant participants automatically. Current real demo path uses a pasted Band room ID or `BAND_DEFAULT_ROOM_ID`. |
| Auth/RLS | Replace temporary env org scope with Supabase auth-derived org scope and harden production RLS policies. |

## Explicitly Out Of Scope For Bootstrap

Per `AGENTS.md`: full RBAC, billing, production queues, OAuth integrations,
Slack/Teams, vendor crawling, complex analytics, perfect parsing, and a general
approval engine.

## Bottom Line

The HR Candidate Screening workflow runs end to end through the web UI, and this
change is wiring the previously hidden Band audit messages and full per-agent
reasoning into the workflow detail page instead of requiring a separate Band room
or report page to understand what happened.
