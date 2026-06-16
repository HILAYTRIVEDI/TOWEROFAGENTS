import Link from "next/link";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { WorkflowRemoveButton } from "@/components/workflow-remove-button";
import { listWorkflows } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function WorkflowsPage() {
  const orgId = process.env.NEXT_PUBLIC_DEFAULT_ORG_ID;
  let error: string | null = null;
  const workflows = orgId
    ? await listWorkflows(orgId).catch((caught) => {
        error = caught instanceof Error ? caught.message : "Workflow loading failed";
        return [];
      })
    : [];

  return (
    <>
      <PageHeader
        eyebrow="Workflow runs"
        title="One record for every decision."
        description="Drafts and active records persisted by the FastAPI and Supabase backend."
        action={
          <Link className="button primary" href="/workflows/new">
            New workflow
          </Link>
        }
      />
      {!orgId ? (
        <p className="notice error" role="alert">
          Set NEXT_PUBLIC_DEFAULT_ORG_ID to load organization workflows.
        </p>
      ) : null}
      {error ? (
        <p className="notice error" role="alert">
          {error}
        </p>
      ) : null}
      {workflows.length > 0 ? (
        <ul className="workflow-list">
          {workflows.map((workflow) => (
            <li className="workflow-row" key={workflow.id}>
              <div>
                <p className="workflow-row-title">
                  <Link href={`/workflows/${workflow.id}`}>{workflow.title}</Link>
                </p>
                <p className="workflow-row-meta">
                  {workflow.template_slug ?? "Unassigned"} ·{" "}
                  {new Date(workflow.created_at).toLocaleString()}
                </p>
              </div>
              <div className="workflow-row-trailing">
                <span className={`status-badge status-${workflow.status}`}>
                  {workflow.status.replaceAll("_", " ")}
                </span>
                <WorkflowRemoveButton
                  title={workflow.title}
                  workflowId={workflow.id}
                />
              </div>
            </li>
          ))}
        </ul>
      ) : orgId && !error ? (
        <EmptyState title="No workflow records yet">
          Create the first workflow. The backend will persist it as a draft.
        </EmptyState>
      ) : null}
    </>
  );
}
