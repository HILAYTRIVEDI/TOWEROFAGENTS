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
  ('engineering-reviewer', 'Engineering Reviewer', 'engineering', 'Reviews change risks and tests.', 'featherless')
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
  )
on conflict (slug) do update
set
  name = excluded.name,
  description = excluded.description,
  depth = excluded.depth,
  agent_slugs = excluded.agent_slugs,
  required_artifacts = excluded.required_artifacts;

