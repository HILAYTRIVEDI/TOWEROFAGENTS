-- Add human-approval gate columns to workflow_reports.
-- Applies only to the HR candidate-screening review flow.
-- review_status: pending_review (default) → approved | rejected
-- reviewer_note: optional free-text justification from the reviewer
-- reviewed_at: timestamp set when a decision is recorded

alter table public.workflow_reports
  add column review_status text not null default 'pending_review'
    check (review_status in ('pending_review', 'approved', 'rejected')),
  add column reviewer_note text,
  add column reviewed_at timestamptz;

comment on column public.workflow_reports.review_status is
  'HR candidate-screening review gate: pending_review → approved | rejected.';
comment on column public.workflow_reports.reviewer_note is
  'Optional note recorded by the human reviewer at decision time.';
comment on column public.workflow_reports.reviewed_at is
  'Timestamp when the approve/reject decision was persisted.';
