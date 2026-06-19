import { WorkflowCreateForm } from "@/components/workflow-create-form";
import { PageHeader } from "@/components/page-header";

export default function NewWorkflowPage() {
  const orgId = process.env.NEXT_PUBLIC_DEFAULT_ORG_ID;

  return (
    <>
      <PageHeader
        eyebrow="New workflow"
        title="Prepare a candidate review."
        description="Create a persisted workflow draft, then upload its required artifacts."
      />
      {orgId ? (
        <WorkflowCreateForm orgId={orgId} />
      ) : (
        <p className="notice error" role="alert">
          Set NEXT_PUBLIC_DEFAULT_ORG_ID before creating workflows.
        </p>
      )}
    </>
  );
}
