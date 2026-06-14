import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";

export default async function WorkflowDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <>
      <PageHeader
        eyebrow={`Workflow ${id}`}
        title="Workflow detail"
        description="This route is reserved for document status, Band messages, agent findings, and execution progress."
      />
      <EmptyState title="Waiting for persistence">
        The base scaffold does not invent workflow data. This page will load the
        typed workflow contract when the API implementation begins.
      </EmptyState>
    </>
  );
}

