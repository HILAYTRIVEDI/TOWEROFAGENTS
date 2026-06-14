# Database Schema

Supabase migrations define:

- Identity and tenancy: `organizations`, `profiles`
- Agent catalog: `agents`, `agent_skills`
- Workflow state: `workflow_templates`, `workflows`, `workflow_agents`
- Knowledge: `documents`, `document_chunks`
- Audit/output: `agent_findings`, `band_messages`, `workflow_reports`, `approvals`, `agent_metrics`

All business records carry organization or workflow scope. `document_chunks.embedding` uses `vector(1536)`. `EMBEDDING_DIMENSIONS` and the selected embedding model must remain at 1536 unless migration `001_init.sql` and vector search function `002_vector_search.sql` are changed together.

The bootstrap establishes tables, indexes, update triggers, basic row-level security, and `match_document_chunks`. Storage bucket policies and production auth policy hardening belong to the data implementation phase.

