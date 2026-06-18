alter table public.documents
  alter column workflow_id drop not null;

alter table public.document_chunks
  alter column workflow_id drop not null;

create index documents_org_shared_idx
  on public.documents (org_id, created_at desc)
  where workflow_id is null;

create or replace function public.match_document_chunks(
  query_embedding vector(1536),
  match_org_id uuid,
  match_workflow_id uuid,
  match_threshold double precision default 0.2,
  match_count integer default 8
)
returns table (
  id uuid,
  document_id uuid,
  content text,
  metadata jsonb,
  similarity double precision
)
language sql
stable
security invoker
set search_path = public
as $$
  select
    dc.id,
    dc.document_id,
    dc.content,
    dc.metadata,
    1 - (dc.embedding <=> query_embedding) as similarity
  from public.document_chunks as dc
  where dc.org_id = match_org_id
    and (dc.workflow_id = match_workflow_id or dc.workflow_id is null)
    and dc.embedding is not null
    and 1 - (dc.embedding <=> query_embedding) >= match_threshold
  order by dc.embedding <=> query_embedding
  limit greatest(1, least(match_count, 50));
$$;

comment on function public.match_document_chunks is
  'Tenant-scoped cosine similarity search over workflow-specific and organization-shared chunks.';
