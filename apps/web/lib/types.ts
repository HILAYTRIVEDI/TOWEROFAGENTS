export type WorkflowStatus =
  | "draft"
  | "indexing"
  | "ready"
  | "running"
  | "awaiting_review"
  | "completed"
  | "failed";

export interface WorkflowCreate {
  org_id: string;
  title: string;
  user_request: string;
  template_slug?: string | null;
}

export interface Workflow {
  id: string;
  org_id: string;
  title: string;
  template_slug?: string | null;
  status: WorkflowStatus;
  band_room_id?: string | null;
  created_at: string;
}

export type DocumentType = "resume" | "jd" | "policy" | "crm" | "code" | "other";

export interface DocumentRead {
  id: string;
  org_id: string;
  workflow_id?: string | null;
  doc_type: DocumentType;
  filename: string;
  mime_type?: string | null;
  status: string;
  created_at: string;
}

export interface AgentDescriptor {
  slug: string;
  name: string;
  category: string;
  description: string;
}

export interface HealthStatus {
  service: string;
  status: string;
  environment: string;
  integrations: Record<string, string>;
}

export interface WorkflowReport {
  id: string;
  workflow_id: string;
  recommendation: string;
  summary: string;
  fit_score?: number | null;
  strengths: string[];
  gaps: string[];
  interview_questions: string[];
  policy_note?: string | null;
  evidence_chunk_ids: string[];
  requires_human_review: boolean;
}
