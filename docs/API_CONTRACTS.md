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
| `POST` | `/workflows/{workflow_id}/documents` | Upload an artifact file to private storage |
| `GET` | `/knowledge/{org_id}/documents` | List organization-shared knowledge documents |
| `POST` | `/knowledge/{org_id}/documents` | Upload an organization-shared knowledge document to private storage |
| `POST` | `/workflows/{workflow_id}/index` | Parse, chunk, embed, and index artifacts |
| `POST` | `/workflows/{workflow_id}/run` | Start orchestration |
| `GET` | `/workflows/{workflow_id}/report` | Get report for workflow |
| `GET` | `/agents` | List registered agents |
| `GET` | `/reports/{report_id}` | Get report by ID |

Workflow create/list/detail persistence is functional through Supabase. Calling `GET /workflows`
without `org_id` returns an empty list to prevent accidental cross-organization disclosure.
`DELETE /workflows/{workflow_id}` permanently removes the workflow row and returns `204 No Content`;
it returns `404` when no matching workflow exists.
The frontend temporarily reads this scope from `NEXT_PUBLIC_DEFAULT_ORG_ID`;
authenticated profile-derived scope will replace it when auth is implemented.

`POST /workflows/{workflow_id}/documents` is a `multipart/form-data` request with a `doc_type`
field (`resume|jd|policy|crm|code|other`) and a `file` part. It uploads the file to the private
Supabase Storage bucket configured by `DOCUMENTS_BUCKET` (default `workflow-documents`) and inserts a
`documents` row scoped to the workflow's organization and workflow.

`GET /knowledge/{org_id}/documents` returns shared organization files where `workflow_id` is
`null`. `POST /knowledge/{org_id}/documents` accepts the same multipart shape as workflow
uploads, stores the object under an organization/shared storage prefix, and inserts a `documents`
row scoped to the organization with `workflow_id: null`. This powers the reusable Knowledge base
documents that should be available across workflows.

Both upload endpoints return `201` with `DocumentRead` (`id`, `org_id`, `workflow_id`, `doc_type`,
`filename`, `mime_type`, `status`, `created_at`). They return `422` for an unknown `doc_type` or
empty file, `413` above the configured `MAX_UPLOAD_BYTES`, `404` for an unknown workflow or
organization, and `503` when Supabase is unconfigured. Parsing, chunking, and embedding are not
performed here — the row lands in `uploaded` status. Index, run, and report generation endpoints
still return `501 Not Implemented`.

## Core Shapes

```json
{
  "create_workflow": {
    "org_id": "uuid",
    "title": "Candidate screening: Jane Doe",
    "user_request": "Assess candidate against role and policy",
    "template_slug": "hr-candidate-screening"
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
    "requires_human_review": true
  }
}
```

Errors use FastAPI's `{"detail": "..."}` shape. Upload limits, supported MIME types, pagination, and auth headers will be finalized during product implementation.
