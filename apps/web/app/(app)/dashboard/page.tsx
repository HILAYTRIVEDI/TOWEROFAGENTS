import { DashboardTabs } from "@/components/dashboard-tabs";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { listWorkflows } from "@/lib/api";
import type { Workflow } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let workflows: Workflow[] = [];
  let loadError = false;
  const orgId = process.env.NEXT_PUBLIC_DEFAULT_ORG_ID;

  try {
    workflows = orgId ? await listWorkflows(orgId) : [];
  } catch {
    loadError = true;
  }

  return (
    <>
      <PageHeader
        eyebrow="Control tower"
        title="Every domain, one view."
        description="Switch between HR, Engineering, Sales, and executive rollups to follow workflow status and agent collaboration as it lands."
      />

      {!orgId ? (
        <p className="notice error" role="alert">
          Set NEXT_PUBLIC_DEFAULT_ORG_ID to load organization workflows.
        </p>
      ) : null}

      {loadError ? (
        <p className="notice error" role="alert">
          Workflow data could not be loaded from the API. Showing an empty
          dashboard -- start the API or check NEXT_PUBLIC_API_BASE_URL.
        </p>
      ) : null}

      {orgId && !loadError && workflows.length === 0 ? (
        <EmptyState actionHref="/workflows/new" title="No workflows yet">
          Create a workflow from the workflow library to see it appear here,
          grouped by domain.
        </EmptyState>
      ) : null}

      <DashboardTabs workflows={workflows} />
    </>
  );
}
