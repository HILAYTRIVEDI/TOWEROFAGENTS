import type {
  AgentDescriptor,
  DocumentRecord,
  HealthStatus,
  Workflow,
  WorkflowCreate,
  WorkflowReport,
} from "@/lib/types";

const PUBLIC_API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function apiBaseUrl(): string {
  if (typeof window === "undefined") {
    return process.env.API_BASE_URL ?? PUBLIC_API_BASE_URL;
  }
  return PUBLIC_API_BASE_URL;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new ApiError(
      body?.detail ?? `API request failed (${response.status})`,
      response.status,
    );
  }

  return (await response.json()) as T;
}

export function getHealth(): Promise<HealthStatus> {
  return apiRequest("/health", { cache: "no-store" });
}

export function listAgents(): Promise<AgentDescriptor[]> {
  return apiRequest("/agents", { next: { revalidate: 60 } });
}

export function listWorkflows(orgId: string): Promise<Workflow[]> {
  return apiRequest(`/workflows?org_id=${encodeURIComponent(orgId)}`, {
    cache: "no-store",
  });
}

export function getWorkflow(workflowId: string): Promise<Workflow> {
  return apiRequest(`/workflows/${workflowId}`, { cache: "no-store" });
}

export function createWorkflow(payload: WorkflowCreate): Promise<Workflow> {
  return apiRequest("/workflows", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function uploadDocument(
  workflowId: string,
  docType: string,
  file: File,
): Promise<DocumentRecord> {
  const body = new FormData();
  body.set("doc_type", docType);
  body.set("file", file);
  return apiRequest(`/workflows/${workflowId}/documents`, {
    method: "POST",
    body,
  });
}

export function getWorkflowReport(workflowId: string): Promise<WorkflowReport> {
  return apiRequest(`/workflows/${workflowId}/report`, { cache: "no-store" });
}

export function getReport(reportId: string): Promise<WorkflowReport> {
  return apiRequest(`/reports/${reportId}`, { cache: "no-store" });
}
