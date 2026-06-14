-- Storage bucket for uploaded workflow artifacts (resumes, JDs, policies, CRM
-- notes, code). These are confidential, so the bucket is PRIVATE (public =
-- false): no anonymous read access, and no public storage RLS policy is
-- granted here. Server-side uploads use the Supabase service role key, which
-- bypasses storage RLS. That key must never reach the Next.js browser client.
insert into storage.buckets (id, name, public)
values ('workflow-documents', 'workflow-documents', false)
on conflict (id) do nothing;
