# API Contracts

Base URL: `http://localhost:8000`. JSON fields use snake case. Protected endpoints will derive organization scope from Supabase auth when auth is implemented; temporary bootstrap requests carry `org_id`.

## Endpoints

| Method | Path | Response |
|---|---|---|
| `GET` | `/health` | Service and dependency configuration status |
| `POST` | `/workflows` | Create a workflow |
| `GET` | `/workflows?org_id={org_id}` | List organization-scoped workflows |
| `GET` | `/workflows/{workflow_id}` | Workflow detail |
| `POST` | `/workflows/{workflow_id}/documents` | Upload an artifact file to private storage |
| `POST` | `/workflows/{workflow_id}/index` | Parse, chunk, embed, and index artifacts |
| `POST` | `/workflows/{workflow_id}/run` | Start orchestration |
| `GET` | `/workflows/{workflow_id}/report` | Get report for workflow |
| `GET` | `/agents` | List registered agents |
| `GET` | `/reports/{report_id}` | Get report by ID |

Workflow create/list/detail persistence is functional through Supabase. Calling `GET /workflows`
without `org_id` returns an empty list to prevent accidental cross-organization disclosure.
The frontend temporarily reads this scope from `NEXT_PUBLIC_DEFAULT_ORG_ID`;
authenticated profile-derived scope will replace it when auth is implemented.

`POST /workflows/{workflow_id}/documents` is a `multipart/form-data` request with a `doc_type`
field (`resume|jd|policy|crm|code|other`) and a `file` part. It uploads the file to the private
`workflow-documents` Supabase Storage bucket and inserts a `documents` row scoped to the workflow's
organization, returning `201` with `DocumentRead` (`id`, `workflow_id`, `filename`, `mime_type`,
`status`, `created_at`). It returns `422` for an unknown `doc_type` or empty file, `413` above the
configured `MAX_UPLOAD_BYTES`, `404` for an unknown workflow, and `503` when Supabase is
unconfigured. Parsing, chunking, and embedding are not performed here — the row lands in `uploaded`
status. Index, run, and report generation endpoints still return `501 Not Implemented`.

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
