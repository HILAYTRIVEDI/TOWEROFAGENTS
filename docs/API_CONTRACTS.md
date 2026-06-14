# API Contracts

Base URL: `http://localhost:8000`. JSON fields use snake case. Protected endpoints will derive organization scope from Supabase auth when auth is implemented; temporary bootstrap requests carry `org_id`.

## Endpoints

| Method | Path | Response |
|---|---|---|
| `GET` | `/health` | Service and dependency configuration status |
| `POST` | `/workflows` | Create a workflow |
| `GET` | `/workflows` | List workflows |
| `GET` | `/workflows/{workflow_id}` | Workflow detail |
| `POST` | `/workflows/{workflow_id}/documents` | Upload artifact metadata/file |
| `POST` | `/workflows/{workflow_id}/index` | Parse, chunk, embed, and index artifacts |
| `POST` | `/workflows/{workflow_id}/run` | Start orchestration |
| `GET` | `/workflows/{workflow_id}/report` | Get report for workflow |
| `GET` | `/agents` | List registered agents |
| `GET` | `/reports/{report_id}` | Get report by ID |

Only `/health` and static agent/template metadata are functional in the bootstrap. Product endpoints return `501 Not Implemented` rather than fake success.

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

