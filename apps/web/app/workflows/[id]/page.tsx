import Link from "next/link";
import { notFound } from "next/navigation";

import { DocumentUpload } from "@/components/document-upload";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { ApiError, getWorkflow } from "@/lib/api";

export default async function WorkflowDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const workflow = await getWorkflow(id).catch((error) => {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  });

  return (
    <>
      <PageHeader
        eyebrow={`Workflow ${workflow.status.replaceAll("_", " ")}`}
        title={workflow.title}
        description={`Template: ${workflow.template_slug ?? "Unassigned"} · Created ${new Date(workflow.created_at).toLocaleString()}`}
      />
      <section className="detail-grid">
        <article className="detail-card">
          <p className="eyebrow">Record</p>
          <dl>
            <div>
              <dt>Workflow ID</dt>
              <dd>{workflow.id}</dd>
            </div>
            <div>
              <dt>Organization</dt>
              <dd>{workflow.org_id}</dd>
            </div>
            <div>
              <dt>Band room</dt>
              <dd>{workflow.band_room_id ?? "Not assigned"}</dd>
            </div>
          </dl>
        </article>
        <article className="detail-card">
          <DocumentUpload scope="workflow" workflowId={workflow.id} />
        </article>
      </section>
      <EmptyState title="Execution is not implemented yet">
        Uploaded files are stored privately, but indexing and workflow execution
        still return 501. The UI will not claim that an agent review has run.{" "}
        <Link href={`/reports/${workflow.id}`}>View report state</Link>.
      </EmptyState>
    </>
  );
}
