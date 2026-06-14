import Link from "next/link";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";

export default function WorkflowsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Workflow runs"
        title="One record for every decision."
        description="Persistence is the next implementation phase. This view is ready for API-backed workflow records."
        action={
          <Link className="button primary" href="/workflows/new">
            New workflow
          </Link>
        }
      />
      <EmptyState title="No workflow records yet">
        The base scaffold does not create synthetic runs. Once persistence is
        connected, drafts and active runs will appear here.
      </EmptyState>
    </>
  );
}

