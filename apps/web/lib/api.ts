import type {
  AgentDescriptor,
  Workflow,
  WorkflowCreate,
  WorkflowReport,
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(body?.detail ?? `API request failed (${response.status})`);
  }

  return (await response.json()) as T;
}

export function listAgents(): Promise<AgentDescriptor[]> {
  return apiRequest("/agents", { next: { revalidate: 60 } });
}

export function listWorkflows(): Promise<Workflow[]> {
  return apiRequest("/workflows", { cache: "no-store" });
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

export function getWorkflowReport(workflowId: string): Promise<WorkflowReport> {
  return apiRequest(`/workflows/${workflowId}/report`, { cache: "no-store" });
}

export function getReport(reportId: string): Promise<WorkflowReport> {
  return apiRequest(`/reports/${reportId}`, { cache: "no-store" });
}

