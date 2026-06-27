# Database Schema

Supabase migrations define:

- Identity and tenancy: `organizations`, `profiles`
- Agent catalog: `agents`, `agent_skills`
- Workflow state: `workflow_templates`, `workflows`, `workflow_agents`
- Knowledge: `documents`, `document_chunks`
- Audit/output: `agent_findings`, `band_messages`, `workflow_reports`, `approvals`, `agent_metrics`

All business records carry organization or workflow scope. `document_chunks.embedding` uses `vector(1536)`. `EMBEDDING_DIMENSIONS` and the selected embedding model must remain at 1536 unless migration `001_init.sql`, vector search functions `002_vector_search.sql` / `004_organization_documents.sql`, and any live Supabase schema are changed together.

The bootstrap establishes tables, indexes, update triggers, basic row-level security, and `match_document_chunks`. Migration `003_documents_storage.sql` creates the private `workflow-documents` Storage bucket used by the document upload endpoint; uploads run server-side with the service role key (which bypasses storage RLS), so no public storage policy is granted. `DOCUMENTS_BUCKET` can override the bucket name at runtime.

Migration `004_organization_documents.sql` allows `documents.workflow_id` and `document_chunks.workflow_id` to be nullable. Rows with `workflow_id = null` are organization-shared Knowledge uploads; workflow rows remain workflow-specific. `match_document_chunks` now returns both workflow-specific chunks and organization-shared chunks for the same organization once indexing is wired. Per-role storage RLS policies and production auth policy hardening belong to the data implementation phase.
