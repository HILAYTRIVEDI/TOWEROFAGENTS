insert into public.agents (slug, name, category, description, provider_preference)
values
  ('workflow-router', 'Workflow Router', 'platform', 'Selects templates and agents.', 'aiml'),
  ('rag-retriever', 'RAG Retriever', 'platform', 'Builds scoped evidence packs.', null),
  ('policy-guardian', 'Policy Guardian', 'platform', 'Checks policy and escalation rules.', 'featherless'),
  ('final-decision', 'Final Decision Agent', 'platform', 'Synthesizes verified reports.', 'aiml'),
  ('resume-jd-matcher', 'Resume/JD Matcher', 'hr', 'Compares evidence with role requirements.', 'aiml'),
  ('bias-reviewer', 'Bias/Safety Reviewer', 'hr', 'Reviews sensitive and unsupported reasoning.', 'featherless'),
  ('interview-planner', 'Interview Planner', 'hr', 'Creates evidence-linked interview questions.', 'aiml'),
  ('lead-qualifier', 'Lead Qualifier', 'sales', 'Scores ICP fit and next actions.', 'aiml'),
  ('engineering-reviewer', 'Engineering Reviewer', 'engineering', 'Reviews change risks and tests.', 'featherless'),
  ('procurement-review', 'Procurement Agent', 'vendor', 'Reviews business need, pricing, and procurement policy fit.', 'aiml'),
  ('legal-review', 'Legal Agent', 'vendor', 'Reviews contract risks and terms.', 'aiml'),
  ('security-review', 'Security Agent', 'vendor', 'Reviews data/security risks and missing security documentation.', 'aiml'),
  ('finance-review', 'Finance Agent', 'vendor', 'Reviews budget and cost concerns.', 'aiml'),
  ('compliance-review', 'Compliance Agent', 'vendor', 'Reviews policy and regulatory fit.', 'aiml'),
  ('vendor-controller', 'Controller Agent', 'vendor', 'Synthesizes specialist findings into a final vendor recommendation.', 'aiml')
on conflict (slug) do update
set
  name = excluded.name,
  category = excluded.category,
  description = excluded.description,
  provider_preference = excluded.provider_preference;

insert into public.workflow_templates (
  slug,
  name,
  description,
  depth,
  agent_slugs,
  required_artifacts
)
values
  (
    'hr-candidate-screening',
    'HR Candidate Screening',
    'Evidence-backed candidate review with fairness and policy gates.',
    'deep',
    '["workflow-router","rag-retriever","resume-jd-matcher","bias-reviewer","interview-planner","policy-guardian","final-decision"]'::jsonb,
    '["resume","job_description","hiring_policy"]'::jsonb
  ),
  (
    'sales-lead-qualification',
    'Sales Lead Qualification',
    'Lightweight ICP scoring and outreach recommendation.',
    'shallow',
    '["lead-qualifier","rag-retriever","final-decision"]'::jsonb,
    '["crm_notes"]'::jsonb
  ),
  (
    'engineering-change-review',
    'Engineering Change Review',
    'Lightweight code change risk and test review.',
    'shallow',
    '["engineering-reviewer","policy-guardian","final-decision"]'::jsonb,
    '["code_diff"]'::jsonb
  ),
  (
    'vendor-onboarding-review',
    'Vendor Onboarding Review',
    'Reviews a prospective vendor across procurement, legal, security, finance, and compliance, then produces a decision packet for human approval.',
    'deep',
    '["workflow-router","rag-retriever","procurement-review","legal-review","security-review","finance-review","compliance-review","vendor-controller"]'::jsonb,
    '["vendor_profile","contract","security_documentation","pricing"]'::jsonb
  )
on conflict (slug) do update
set
  name = excluded.name,
  description = excluded.description,
  depth = excluded.depth,
  agent_slugs = excluded.agent_slugs,
  required_artifacts = excluded.required_artifacts;

-- Keep demo seed data executable until a dedicated schema migration owns these
-- vendor doc types.
alter table public.documents
  drop constraint if exists documents_doc_type_check;

alter table public.documents
  add constraint documents_doc_type_check
  check (doc_type in (
    'resume',
    'jd',
    'policy',
    'crm',
    'code',
    'other',
    'vendor_profile',
    'contract',
    'security_documentation',
    'pricing'
  ));

insert into public.organizations (id, name, slug)
values
  (
    '22222222-2222-2222-2222-222222222222',
    'Acme Demo Organization',
    'acme-demo'
  )
on conflict (slug) do update
set
  name = excluded.name;

insert into public.workflows (
  id,
  org_id,
  template_id,
  title,
  user_request,
  status,
  metadata
)
values
  (
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    (
      select id
      from public.workflow_templates
      where slug = 'vendor-onboarding-review'
    ),
    'Review Acme Analytics vendor onboarding',
    'Review fictional vendor Acme Analytics for procurement onboarding using the supplied vendor profile, contract excerpt, and pricing sheet.',
    'ready',
    '{"demo": true, "vendor_name": "Acme Analytics"}'::jsonb
  )
on conflict (id) do update
set
  org_id = excluded.org_id,
  template_id = excluded.template_id,
  title = excluded.title,
  user_request = excluded.user_request,
  status = excluded.status,
  metadata = excluded.metadata;

insert into public.documents (
  id,
  org_id,
  workflow_id,
  doc_type,
  filename,
  storage_path,
  mime_type,
  size_bytes,
  content_hash,
  status,
  metadata
)
values
  (
    '33333333-3333-3333-3333-333333333331',
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'vendor_profile',
    'acme-analytics-vendor-profile.txt',
    '11111111-1111-1111-1111-111111111111/demo/acme-analytics-vendor-profile.txt',
    'text/plain',
    620,
    'demo-acme-analytics-vendor-profile',
    'indexed',
    '{"demo": true, "vendor_name": "Acme Analytics"}'::jsonb
  ),
  (
    '33333333-3333-3333-3333-333333333332',
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'contract',
    'acme-analytics-contract-excerpt.txt',
    '11111111-1111-1111-1111-111111111111/demo/acme-analytics-contract-excerpt.txt',
    'text/plain',
    760,
    'demo-acme-analytics-contract-excerpt',
    'indexed',
    '{"demo": true, "vendor_name": "Acme Analytics"}'::jsonb
  ),
  (
    '33333333-3333-3333-3333-333333333333',
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'pricing',
    'acme-analytics-pricing-sheet.txt',
    '11111111-1111-1111-1111-111111111111/demo/acme-analytics-pricing-sheet.txt',
    'text/plain',
    560,
    'demo-acme-analytics-pricing-sheet',
    'indexed',
    '{"demo": true, "vendor_name": "Acme Analytics"}'::jsonb
  )
on conflict (id) do update
set
  org_id = excluded.org_id,
  workflow_id = excluded.workflow_id,
  doc_type = excluded.doc_type,
  filename = excluded.filename,
  storage_path = excluded.storage_path,
  mime_type = excluded.mime_type,
  size_bytes = excluded.size_bytes,
  content_hash = excluded.content_hash,
  status = excluded.status,
  metadata = excluded.metadata;

insert into public.document_chunks (
  id,
  document_id,
  org_id,
  workflow_id,
  chunk_index,
  content,
  metadata
)
values
  (
    '44444444-4444-4444-4444-444444444441',
    '33333333-3333-3333-3333-333333333331',
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    0,
    'Acme Analytics is a fictional vendor offering spend analytics dashboards and invoice anomaly detection for procurement teams. The proposed business use is quarterly supplier-spend review for the finance operations group. The request owner expects 25 internal users during the pilot.',
    '{"doc_type": "vendor_profile", "filename": "acme-analytics-vendor-profile.txt", "vendor_name": "Acme Analytics"}'::jsonb
  ),
  (
    '44444444-4444-4444-4444-444444444442',
    '33333333-3333-3333-3333-333333333331',
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    1,
    'Acme Analytics states that customer data used in the pilot will be limited to supplier names, invoice totals, payment dates, and category labels. No bank account numbers or personal employee data are expected in the pilot data set.',
    '{"doc_type": "vendor_profile", "filename": "acme-analytics-vendor-profile.txt", "vendor_name": "Acme Analytics"}'::jsonb
  ),
  (
    '44444444-4444-4444-4444-444444444443',
    '33333333-3333-3333-3333-333333333332',
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    0,
    'Contract excerpt: Acme Analytics offers a 12-month subscription with termination for convenience on 30 days notice after the first 90 days. Payment terms are net-60 from receipt of invoice. Each party provides mutual indemnity for third-party claims caused by its breach, negligence, or willful misconduct.',
    '{"doc_type": "contract", "filename": "acme-analytics-contract-excerpt.txt", "vendor_name": "Acme Analytics"}'::jsonb
  ),
  (
    '44444444-4444-4444-4444-444444444444',
    '33333333-3333-3333-3333-333333333332',
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    1,
    'Contract excerpt: Acme Analytics may use aggregated and de-identified usage statistics to improve the service. The excerpt does not include a security attestation, audit report, breach notification window, or data residency commitment.',
    '{"doc_type": "contract", "filename": "acme-analytics-contract-excerpt.txt", "vendor_name": "Acme Analytics"}'::jsonb
  ),
  (
    '44444444-4444-4444-4444-444444444445',
    '33333333-3333-3333-3333-333333333333',
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    0,
    'Pricing sheet: Acme Analytics pilot pricing is 25 seats at 120 dollars per user per month, billed annually after a 60-day no-cost evaluation. Implementation support is a one-time 4,000 dollar fee. The vendor offers a 10 percent discount if the annual contract is signed before quarter end.',
    '{"doc_type": "pricing", "filename": "acme-analytics-pricing-sheet.txt", "vendor_name": "Acme Analytics"}'::jsonb
  ),
  (
    '44444444-4444-4444-4444-444444444446',
    '33333333-3333-3333-3333-333333333333',
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    1,
    'Pricing sheet: The expected annual subscription after discount is 32,400 dollars plus the 4,000 dollar implementation fee. Renewal pricing may increase by up to 5 percent annually. Travel expenses are not applicable for the remote implementation.',
    '{"doc_type": "pricing", "filename": "acme-analytics-pricing-sheet.txt", "vendor_name": "Acme Analytics"}'::jsonb
  )
on conflict (document_id, chunk_index) do update
set
  id = excluded.id,
  org_id = excluded.org_id,
  workflow_id = excluded.workflow_id,
  content = excluded.content,
  metadata = excluded.metadata;
