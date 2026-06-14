import { DashboardTabs } from "@/components/dashboard-tabs";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { listWorkflows } from "@/lib/api";
import type { Workflow } from "@/lib/types";

export default async function DashboardPage() {
  let workflows: Workflow[] = [];
  let loadError = false;

  try {
    workflows = await listWorkflows();
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

      {loadError && (
        <p className="notice error" role="alert">
          Workflow data could not be loaded from the API. Showing an empty
          dashboard -- start the API or check NEXT_PUBLIC_API_BASE_URL.
        </p>
      )}

      {!loadError && workflows.length === 0 && (
        <EmptyState title="No workflows yet">
          Create a workflow from the workflow library to see it appear here,
          grouped by domain.
        </EmptyState>
      )}

      <DashboardTabs workflows={workflows} />
    </>
  );
}
