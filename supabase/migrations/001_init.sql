create extension if not exists pgcrypto;
create extension if not exists vector;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  org_id uuid not null references public.organizations(id) on delete cascade,
  display_name text,
  role text not null default 'member' check (role in ('owner', 'admin', 'member', 'viewer')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.agents (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  category text not null,
  description text not null default '',
  provider_preference text,
  enabled boolean not null default true,
  configuration jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.agent_skills (
  id uuid primary key default gen_random_uuid(),
  agent_id uuid not null references public.agents(id) on delete cascade,
  skill text not null,
  description text,
  created_at timestamptz not null default now(),
  unique (agent_id, skill)
);

create table public.workflow_templates (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  description text not null default '',
  depth text not null check (depth in ('deep', 'shallow')),
  agent_slugs jsonb not null default '[]'::jsonb,
  required_artifacts jsonb not null default '[]'::jsonb,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.workflows (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  template_id uuid references public.workflow_templates(id) on delete set null,
  created_by uuid references public.profiles(id) on delete set null,
  title text not null,
  user_request text not null,
  status text not null default 'draft'
    check (status in (
      'draft', 'indexing', 'ready', 'running', 'awaiting_review', 'completed', 'failed'
    )),
  band_room_id text,
  error_message text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.workflow_agents (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  workflow_id uuid not null references public.workflows(id) on delete cascade,
  agent_id uuid not null references public.agents(id) on delete restrict,
  execution_order integer,
  status text not null default 'assigned'
    check (status in ('assigned', 'running', 'completed', 'failed', 'skipped')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workflow_id, agent_id)
);

create table public.documents (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  workflow_id uuid not null references public.workflows(id) on delete cascade,
  uploaded_by uuid references public.profiles(id) on delete set null,
  doc_type text not null default 'other'
    check (doc_type in ('resume', 'jd', 'policy', 'crm', 'code', 'other')),
  filename text not null,
  storage_path text not null,
  mime_type text,
  size_bytes bigint check (size_bytes is null or size_bytes >= 0),
  content_hash text,
  status text not null default 'uploaded'
    check (status in ('uploaded', 'parsing', 'indexed', 'failed')),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Embedding dimension is an architecture constant. Update this and 002 together.
create table public.document_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  org_id uuid not null references public.organizations(id) on delete cascade,
  workflow_id uuid not null references public.workflows(id) on delete cascade,
  chunk_index integer not null check (chunk_index >= 0),
  content text not null,
  metadata jsonb not null default '{}'::jsonb,
  embedding vector(1536),
  created_at timestamptz not null default now(),
  unique (document_id, chunk_index)
);

create table public.agent_findings (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  workflow_id uuid not null references public.workflows(id) on delete cascade,
  workflow_agent_id uuid references public.workflow_agents(id) on delete set null,
  agent_slug text not null,
  finding_type text not null,
  severity text not null check (severity in ('info', 'low', 'medium', 'high', 'critical')),
  title text not null,
  content text not null,
  evidence_chunk_ids uuid[] not null default '{}',
  confidence double precision not null default 0
    check (confidence >= 0 and confidence <= 1),
  requires_human_review boolean not null default false,
  raw_output jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table public.band_messages (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  workflow_id uuid not null references public.workflows(id) on delete cascade,
  band_message_id text,
  band_room_id text not null,
  sender_type text not null check (sender_type in ('human', 'agent', 'system')),
  sender_ref text,
  content text not null,
  message_type text not null default 'message',
  raw_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (band_message_id)
);

create table public.workflow_reports (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  workflow_id uuid not null references public.workflows(id) on delete cascade,
  recommendation text not null,
  summary text not null,
  fit_score double precision check (fit_score is null or (fit_score >= 0 and fit_score <= 100)),
  strengths jsonb not null default '[]'::jsonb,
  gaps jsonb not null default '[]'::jsonb,
  interview_questions jsonb not null default '[]'::jsonb,
  policy_note text,
  evidence_chunk_ids uuid[] not null default '{}',
  requires_human_review boolean not null default true,
  report_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (workflow_id)
);

create table public.approvals (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  workflow_id uuid not null references public.workflows(id) on delete cascade,
  report_id uuid references public.workflow_reports(id) on delete cascade,
  reviewer_id uuid references public.profiles(id) on delete set null,
  status text not null default 'pending'
    check (status in ('pending', 'approved', 'rejected', 'changes_requested')),
  note text,
  decided_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.agent_metrics (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  workflow_id uuid not null references public.workflows(id) on delete cascade,
  agent_slug text not null,
  provider text,
  model text,
  latency_ms integer check (latency_ms is null or latency_ms >= 0),
  input_tokens integer check (input_tokens is null or input_tokens >= 0),
  output_tokens integer check (output_tokens is null or output_tokens >= 0),
  estimated_cost_usd numeric(12, 6) check (
    estimated_cost_usd is null or estimated_cost_usd >= 0
  ),
  success boolean not null,
  error_code text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index workflows_org_created_idx on public.workflows (org_id, created_at desc);
create index documents_workflow_idx on public.documents (workflow_id, created_at);
create index document_chunks_scope_idx on public.document_chunks (org_id, workflow_id);
create index findings_workflow_idx on public.agent_findings (workflow_id, created_at);
create index band_messages_workflow_idx on public.band_messages (workflow_id, created_at);
create index metrics_workflow_idx on public.agent_metrics (workflow_id, created_at);

create trigger organizations_set_updated_at
before update on public.organizations
for each row execute function public.set_updated_at();

create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

create trigger agents_set_updated_at
before update on public.agents
for each row execute function public.set_updated_at();

create trigger workflow_templates_set_updated_at
before update on public.workflow_templates
for each row execute function public.set_updated_at();

create trigger workflows_set_updated_at
before update on public.workflows
for each row execute function public.set_updated_at();

create trigger workflow_agents_set_updated_at
before update on public.workflow_agents
for each row execute function public.set_updated_at();

create trigger documents_set_updated_at
before update on public.documents
for each row execute function public.set_updated_at();

create trigger workflow_reports_set_updated_at
before update on public.workflow_reports
for each row execute function public.set_updated_at();

create trigger approvals_set_updated_at
before update on public.approvals
for each row execute function public.set_updated_at();

alter table public.organizations enable row level security;
alter table public.profiles enable row level security;
alter table public.agents enable row level security;
alter table public.agent_skills enable row level security;
alter table public.workflow_templates enable row level security;
alter table public.workflows enable row level security;
alter table public.workflow_agents enable row level security;
alter table public.documents enable row level security;
alter table public.document_chunks enable row level security;
alter table public.agent_findings enable row level security;
alter table public.band_messages enable row level security;
alter table public.workflow_reports enable row level security;
alter table public.approvals enable row level security;
alter table public.agent_metrics enable row level security;

comment on table public.document_chunks is
  'Workflow-scoped RAG chunks. embedding is fixed at 1536 dimensions for the MVP.';

