# API Contracts

Base URL: `http://localhost:8000`. JSON fields use snake case. Protected endpoints will derive organization scope from Supabase auth when auth is implemented; temporary bootstrap requests carry `org_id`.

## Endpoints

| Method | Path | Response |
|---|---|---|
| `GET` | `/health` | Service and dependency configuration status |
| `POST` | `/workflows` | Create a workflow |
| `GET` | `/workflows?org_id={org_id}` | List organization-scoped workflows |
| `GET` | `/workflows/{workflow_id}` | Workflow detail |
| `DELETE` | `/workflows/{workflow_id}` | Permanently remove a workflow |
| `POST` | `/workflows/{workflow_id}/band-session` | Assign a Band discussion room/session |
| `POST` | `/workflows/{workflow_id}/documents` | Upload an artifact file to private storage |
| `GET` | `/workflows/{workflow_id}/documents` | List workflow artifact upload history |
| `DELETE` | `/workflows/{workflow_id}/documents/{document_id}` | Remove a workflow artifact |
| `GET` | `/knowledge/{org_id}/documents` | List organization-scoped documents |
| `POST` | `/knowledge/{org_id}/documents` | Upload an organization-shared knowledge document to private storage |
| `DELETE` | `/knowledge/{org_id}/documents/{document_id}` | Remove an organization-scoped document |
| `POST` | `/workflows/{workflow_id}/index` | Parse, chunk, embed, and index artifacts |
| `POST` | `/workflows/{workflow_id}/run` | Start orchestration |
| `GET` | `/workflows/{workflow_id}/report` | Get report for workflow |
| `GET` | `/workflows/{workflow_id}/messages` | Get persisted Band discussion/audit messages |
| `GET` | `/workflows/{workflow_id}/findings` | Get persisted per-agent findings/reasoning |
| `GET` | `/agents` | List registered agents |
| `GET` | `/reports/{report_id}` | Get report by ID |

Workflow create/list/detail persistence is functional through Supabase. Calling `GET /workflows`
without `org_id` returns an empty list to prevent accidental cross-organization disclosure.
`DELETE /workflows/{workflow_id}` permanently removes the workflow row and returns `204 No Content`;
it returns `404` when no matching workflow exists.
`POST /workflows/{workflow_id}/band-session` assigns a separate Band discussion room to a workflow.
Pass `{ "band_room_id": "..." }` for a real Band room/session created in Band.ai. In mock mode only,
`{ "create_mock_session": true }` creates a clearly labelled mock room. Automatic real Band room
creation is not implemented in the request-scoped API path.
The frontend temporarily reads this scope from `NEXT_PUBLIC_DEFAULT_ORG_ID`;
authenticated profile-derived scope will replace it when auth is implemented.

`POST /workflows/{workflow_id}/documents` is a `multipart/form-data` request with a `doc_type`
field (`resume|jd|policy|crm|code|other`) and a `file` part. It uploads the file to the private
Supabase Storage bucket configured by `DOCUMENTS_BUCKET` (default `workflow-documents`) and inserts a
`documents` row scoped to the workflow's organization and workflow.
`GET /workflows/{workflow_id}/documents` returns that workflow's artifact history ordered newest
first; the workflow detail UI groups this list by document type tabs.
`DELETE /workflows/{workflow_id}/documents/{document_id}` removes a workflow-scoped artifact and its
private Storage object. It only deletes when both the workflow ID and document ID match, returns
`204` on success, and returns `404` for missing or cross-workflow documents.

`GET /knowledge/{org_id}/documents` returns all document rows scoped to the organization, including
both shared Knowledge uploads and workflow-specific artifacts. `POST /knowledge/{org_id}/documents`
accepts the same multipart shape as workflow uploads, stores the object under an organization/shared
storage prefix, and inserts a `documents` row scoped to the organization with `workflow_id: null`.
This powers reusable Knowledge base documents that should be available across workflows.

Both upload endpoints return `201` with `DocumentRead` (`id`, `org_id`, `workflow_id`, `doc_type`,
`filename`, `mime_type`, `status`, `created_at`). They return `422` for an unknown `doc_type` or
empty file, `413` above the configured `MAX_UPLOAD_BYTES`, `404` for an unknown workflow or
organization, and `503` when Supabase is unconfigured.

After the `201` response, both endpoints schedule ingestion as a background task: the stored
document is downloaded, parsed (`txt|md|pdf|docx`), chunked, embedded via the configured embedding
provider, and written to `document_chunks`. The `documents.status` field transitions
`uploaded → parsing → indexed`, or `→ failed` if parsing/embedding fails (the failure is recorded on
the row and surfaced via the document read endpoints, never raised to the upload caller).
Workflow-scoped chunks carry the owning `workflow_id`; organization-shared chunks are stored with
`workflow_id: null` so `match_document_chunks` returns them across every workflow in the
organization. Embedding vectors are exactly `EMBEDDING_DIMENSIONS` long, matching the `vector(N)`
column; provider responses with any other size fail before chunks are written. When the embedding
provider is unconfigured, ingestion fails loudly and the document is marked `failed` rather than
silently indexed.

`POST /workflows/{workflow_id}/index` re-indexes every document attached to the workflow (idempotent:
each document's existing chunks are replaced). It returns `202 Accepted` with
`{ "status": "accepted", "workflow_id", "documents": "<count>" }`, or `404` for an unknown workflow.

`POST /workflows/{workflow_id}/run` executes the configured workflow specialists against workflow
metadata, the current organization-scoped document inventory, and retrieved chunks from
workflow-specific plus organization-shared Knowledge documents. It persists the packet to
`workflow_reports`, stores each full specialist finding in `agent_findings`, and moves the workflow
to `awaiting_review`. When `workflow.band_room_id` or `BAND_DEFAULT_ROOM_ID` is set, it also posts
and persists the Band audit discussion. Band failures are recorded in `report_payload.band_audit`;
Band and finding-persistence failures never fail the workflow run. It returns `202 Accepted` with
`{ "status": "awaiting_review", "workflow_id", "report_id" }`, or `404` for an unknown workflow.
Reports are explicitly `human_review_required`; evidence chunk IDs come only from retrieved context
and are not invented.
For the `vendor-onboarding-review` template, the persisted `report_payload` also includes
`decision_packet`. This reusable packet is assembled from ordered agent findings by
`build_decision_packet(...)` and is intended as the pattern for future enterprise approval workflows.
Its recommendation is parsed from the controller finding's `RECOMMENDATION:` line and falls back to
`needs_review` when the controller is absent, mock-backed, or emits no parseable recommendation.

`GET /workflows/{workflow_id}/report` returns the persisted report for a workflow. `GET
/reports/{report_id}` returns the same report by ID. Both return `404` when the report is missing.
`GET /workflows/{workflow_id}/messages` returns persisted Band audit messages ordered by
`created_at`; `raw_payload.mode` is the canonical real/mock/failed/skipped indicator for display.
`GET /workflows/{workflow_id}/findings` returns persisted specialist findings ordered by
`created_at`; full reasoning is in `content`, and placeholder/mock findings retain
`confidence: 0`.

`DELETE /knowledge/{org_id}/documents/{document_id}` removes an organization-scoped document and its
private Storage object. It returns `204` on success and `404` when the document is missing or outside
the organization scope.

## Core Shapes

```json
{
  "create_workflow": {
    "org_id": "uuid",
    "title": "Candidate screening: Jane Doe",
    "user_request": "Assess candidate against role and policy",
    "template_slug": "hr-candidate-screening",
    "band_room_id": "optional-band-room-id"
  }
}
```

```json
{
  "workflow": {
    "id": "uuid",
    "org_id": "uuid",
    "title": "Candidate screening: Jane Doe",
    "template_slug": "hr-candidate-screening",
    "status": "draft",
    "band_room_id": null,
    "created_at": "2026-06-14T00:00:00Z"
  }
}
```

```json
{
  "report": {
    "id": "uuid",
    "workflow_id": "uuid",
    "recommendation": "human_review_required",
    "summary": "string",
    "fit_score": null,
    "strengths": [],
    "gaps": [],
    "interview_questions": [],
    "policy_note": null,
    "evidence_chunk_ids": [],
    "requires_human_review": true,
    "report_payload": {
      "band_audit": {
        "room_id": "band-room-id-or-null",
        "message_count": 0,
        "modes": {}
      },
      "decision_packet": {
        "recommendation": "needs_review",
        "executive_summary": "string",
        "evidence_chunk_ids": [],
        "risks": [],
        "missing_information": [],
        "disagreements": [],
        "next_actions": [],
        "human_approval_required": true,
        "audit_trail": {}
      }
    }
  }
}
```

```json
{
  "band_message": {
    "id": "uuid",
    "workflow_id": "uuid",
    "band_message_id": null,
    "band_room_id": "band-room-id",
    "sender_type": "agent",
    "sender_ref": "workflow-router",
    "content": "@rag-retriever ...",
    "message_type": "message",
    "raw_payload": { "mode": "mock" },
    "created_at": "2026-06-14T00:00:00Z"
  }
}
```

```json
{
  "agent_finding": {
    "id": "uuid",
    "workflow_id": "uuid",
    "agent_slug": "resume-jd-matcher",
    "finding_type": "screening",
    "severity": "medium",
    "title": "Relevant experience needs review",
    "content": "Full agent reasoning text.",
    "evidence_chunk_ids": [],
    "confidence": 0.72,
    "requires_human_review": true,
    "raw_output": {},
    "created_at": "2026-06-14T00:00:00Z"
  }
}
```

Errors use FastAPI's `{"detail": "..."}` shape. Upload limits, supported MIME types, pagination, and auth headers will be finalized during product implementation.
