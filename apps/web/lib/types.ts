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
  band_room_id?: string | null;
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

export type DocumentType =
  | "resume"
  | "jd"
  | "policy"
  | "crm"
  | "code"
  | "vendor_profile"
  | "contract"
  | "security_documentation"
  | "pricing"
  | "other";

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

export type ReviewStatus = "pending_review" | "approved" | "rejected";

export interface WorkflowReviewRead {
  report_id: string;
  workflow_id: string;
  review_status: ReviewStatus;
  reviewer_note: string | null;
  reviewed_at: string;
}

export interface DecisionPacketFinding {
  agent_name: string;
  finding_type: string;
  severity: string;
  title: string;
  content: string;
  evidence_chunk_ids: string[];
  confidence: number;
}

export interface DecisionPacket {
  recommendation: "approve" | "reject" | "conditional_approval" | "needs_review";
  executive_summary: string;
  evidence_chunk_ids: string[];
  agent_findings: DecisionPacketFinding[];
  risks: string[];
  missing_information: string[];
  disagreements: string[];
  next_actions: string[];
  human_approval_required: boolean;
  audit_trail: Record<string, unknown>;
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
  review_status: ReviewStatus | null;
  reviewer_note: string | null;
  reviewed_at: string | null;
  report_payload?: {
    band_audit?: {
      room_id?: string | null;
      message_count?: number;
      modes?: Record<string, number>;
      error?: string;
    };
    agents_ran?: string[];
    agents_skipped?: string[];
    any_mock?: boolean;
    decision_packet?: DecisionPacket;
    [key: string]: unknown;
  };
}

export interface BandMessageRead {
  id: string;
  workflow_id: string;
  band_message_id?: string | null;
  band_room_id: string;
  sender_type: string;
  sender_ref?: string | null;
  content: string;
  message_type: string;
  raw_payload: {
    mode?: unknown;
    [key: string]: unknown;
  };
  created_at: string;
}

export interface AgentFindingRead {
  id: string;
  workflow_id: string;
  agent_slug: string;
  finding_type: string;
  severity: string;
  title: string;
  content: string;
  evidence_chunk_ids: string[];
  confidence: number;
  requires_human_review: boolean;
  raw_output?: Record<string, unknown>;
  created_at: string;
}
