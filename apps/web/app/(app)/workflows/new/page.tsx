import { WorkflowCreateForm } from "@/components/workflow-create-form";
import { PageHeader } from "@/components/page-header";

export default async function NewWorkflowPage({
  searchParams,
}: {
  searchParams?: Promise<{ template_slug?: string | string[] }>;
}) {
  const orgId = process.env.NEXT_PUBLIC_DEFAULT_ORG_ID;
  const params = await searchParams;
  const templateSlug = Array.isArray(params?.template_slug)
    ? params?.template_slug[0]
    : params?.template_slug;

  return (
    <>
      <PageHeader
        eyebrow="New workflow"
        title="Prepare a candidate review."
        description="Create a persisted workflow draft, then upload its required artifacts."
      />
      {orgId ? (
        <WorkflowCreateForm initialTemplate={templateSlug} orgId={orgId} />
      ) : (
        <p className="notice error" role="alert">
          Set NEXT_PUBLIC_DEFAULT_ORG_ID before creating workflows.
        </p>
      )}
    </>
  );
}
