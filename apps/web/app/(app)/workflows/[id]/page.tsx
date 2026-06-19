import Link from "next/link";
import { notFound } from "next/navigation";

import { BandSessionForm } from "@/components/band-session-form";
import { DocumentUpload } from "@/components/document-upload";
import { PageHeader } from "@/components/page-header";
import { RunWorkflow } from "@/components/run-workflow";
import { ApiError, getWorkflow, getWorkflowReport } from "@/lib/api";

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

  // Attempt to fetch an existing report so we can link to it; 404 is fine.
  const existingReport = await getWorkflowReport(id).catch((error) => {
    if (error instanceof ApiError && error.status === 404) return null;
    return null;
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
      <article className="detail-card">
        <p className="eyebrow">Band discussion session</p>
        <p className="workflow-row-meta" style={{ marginBottom: "1rem" }}>
          The next run posts the agent handoff discussion, findings, and final
          synthesis into this room.
        </p>
        <BandSessionForm
          currentRoomId={workflow.band_room_id}
          workflowId={workflow.id}
        />
      </article>
      <article className="detail-card">
        <RunWorkflow workflowId={workflow.id} />
        {existingReport ? (
          <p className="workflow-row-meta" style={{ marginTop: "1rem" }}>
            A report already exists for this workflow.{" "}
            <Link href={`/reports/${existingReport.id}`}>
              View latest report
            </Link>
            .
          </p>
        ) : null}
      </article>
    </>
  );
}
