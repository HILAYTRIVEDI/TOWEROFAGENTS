import { DocumentUpload } from "@/components/document-upload";
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
      <DocumentUpload workflowId={id} />
      <EmptyState title="Run output waiting for persistence">
        The base scaffold does not invent workflow data. Band messages, agent
        findings, and execution progress will load from the typed workflow
        contract once run endpoints are implemented.
      </EmptyState>
    </>
  );
}

