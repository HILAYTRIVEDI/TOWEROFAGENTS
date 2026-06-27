import Link from "next/link";
import { notFound } from "next/navigation";

import { BandSessionForm } from "@/components/band-session-form";
import { DocumentUpload } from "@/components/document-upload";
import { PageHeader } from "@/components/page-header";
import { RunWorkflow } from "@/components/run-workflow";
import {
  ApiError,
  getWorkflow,
  getWorkflowFindings,
  getWorkflowMessages,
  getWorkflowReport,
  listWorkflowDocuments,
} from "@/lib/api";
import type { AgentFindingRead, BandMessageRead, DocumentRead } from "@/lib/types";

function messageMode(message: BandMessageRead): string {
  const mode = message.raw_payload.mode;
  return typeof mode === "string" && mode.length > 0 ? mode : "unknown";
}

function isPlaceholderFinding(finding: AgentFindingRead): boolean {
  return finding.confidence === 0 || finding.content.startsWith("[PLACEHOLDER");
}

function cleanWorkflowText(text: string): string {
  return text
    .replaceAll("**", "")
    .replaceAll("##", "")
    .replace(/\s+/g, " ")
    .replace(/\s+(RECOMMENDATION|SUMMARY|EVIDENCE|RISKS):\s*/gi, "\n$1: ")
    .trim();
}

export default async function WorkflowDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [workflow, existingReport, messages, findings, documents] = await Promise.all([
    getWorkflow(id).catch((error) => {
      if (error instanceof ApiError && error.status === 404) {
        notFound();
      }
      throw error;
    }),
    getWorkflowReport(id).catch(() => null),
    getWorkflowMessages(id).catch(() => [] as BandMessageRead[]),
    getWorkflowFindings(id).catch(() => [] as AgentFindingRead[]),
    listWorkflowDocuments(id).catch(() => [] as DocumentRead[]),
  ]);
  const hasMockBandAudit = messages.some((message) => messageMode(message) === "mock");
  const hasPlaceholderDecision =
    existingReport?.report_payload?.any_mock === true || findings.some(isPlaceholderFinding);

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
          <DocumentUpload
            initialDocuments={documents}
            scope="workflow"
            workflowId={workflow.id}
          />
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
      <article className="detail-card">
        <p className="eyebrow">Agent discussion & audit trail</p>
        {hasMockBandAudit ? (
          <p className="notice" style={{ marginBottom: "1rem" }}>
            Some Band audit posts used local test mode because that sender is
            missing live Band credentials. Real decision data is shown
            separately below.
          </p>
        ) : null}
        {messages.length > 0 ? (
          <ul className="workflow-list">
            {messages.map((message) => {
              const mode = messageMode(message);
              return (
                <li className="workflow-row" key={message.id}>
                  <div className="workflow-row-main">
                    <p className="workflow-row-title">
                      {message.sender_ref ?? message.sender_type}
                    </p>
                    <p className="workflow-row-content">
                      {cleanWorkflowText(message.content)}
                    </p>
                    <p className="workflow-row-meta">
                      {new Date(message.created_at).toLocaleString()} · Room{" "}
                      {message.band_room_id}
                    </p>
                  </div>
                  <span className={`status-badge status-${mode}`}>{mode}</span>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="notice">
            No persisted Band discussion messages yet. Run the workflow with a
            Band room or default room configured to capture the audit trail.
          </p>
        )}
      </article>
      <article className="detail-card">
        <p className="eyebrow">Decision & reasoning</p>
        {hasPlaceholderDecision ? (
          <p className="notice error" role="alert">
            Placeholder — model providers not configured. Zero-confidence
            findings are displayed for audit only, not as real decisions.
          </p>
        ) : null}
        {existingReport ? (
          <>
            <p style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <span className={`status-badge status-${existingReport.recommendation}`}>
                {existingReport.recommendation.replaceAll("_", " ")}
              </span>
              {existingReport.review_status ? (
                <span
                  className={`status-badge status-${existingReport.review_status}`}
                  role="status"
                >
                  {existingReport.review_status.replaceAll("_", " ")}
                </span>
              ) : null}
            </p>
            <p className="workflow-row-content" style={{ marginTop: "0.75rem" }}>
              {cleanWorkflowText(existingReport.summary)}
            </p>
            <section className="detail-grid" style={{ marginTop: "1rem" }}>
              <div>
                <p className="eyebrow">Strengths</p>
                {existingReport.strengths.length > 0 ? (
                  <ul className="workflow-list">
                    {existingReport.strengths.map((strength, index) => (
                      <li className="workflow-row" key={index}>
                        {strength}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="notice">None reported.</p>
                )}
              </div>
              <div>
                <p className="eyebrow">Gaps</p>
                {existingReport.gaps.length > 0 ? (
                  <ul className="workflow-list">
                    {existingReport.gaps.map((gap, index) => (
                      <li className="workflow-row" key={index}>
                        {gap}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="notice">None reported.</p>
                )}
              </div>
            </section>
            {existingReport.policy_note ? (
              <section style={{ marginTop: "1rem" }}>
                <p className="eyebrow">Policy note</p>
                <p>{existingReport.policy_note}</p>
              </section>
            ) : null}
            <section style={{ marginTop: "1rem" }}>
              <p className="eyebrow">Interview questions</p>
              {existingReport.interview_questions.length > 0 ? (
                <ol style={{ paddingLeft: "1.25rem" }}>
                  {existingReport.interview_questions.map((question, index) => (
                    <li key={index} style={{ marginBottom: "0.5rem" }}>
                      {question}
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="notice">None reported.</p>
              )}
            </section>
          </>
        ) : (
          <p className="notice">
            No persisted decision packet yet. Run the workflow to capture the
            recommendation and synthesis.
          </p>
        )}
        <section style={{ marginTop: "1rem" }}>
          <p className="eyebrow">Per-agent reasoning</p>
          {findings.length > 0 ? (
            <ul className="workflow-list">
              {findings.map((finding) => {
                const placeholder = isPlaceholderFinding(finding);
                return (
                  <li className="workflow-row" key={finding.id}>
                    <div>
                      <p className="workflow-row-title">{finding.agent_slug}</p>
                      <p>
                        <strong>{finding.title}</strong>
                      </p>
                      <p className="workflow-row-content">
                        {cleanWorkflowText(finding.content)}
                      </p>
                      <p className="workflow-row-meta">
                        {finding.finding_type} · Confidence{" "}
                        {Math.round(finding.confidence * 100)}% ·{" "}
                        {new Date(finding.created_at).toLocaleString()}
                      </p>
                    </div>
                    <span
                      className={`status-badge status-${
                        placeholder ? "mock" : finding.severity
                      }`}
                    >
                      {placeholder ? "mock" : finding.severity}
                    </span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="notice">
              No persisted agent findings yet. Older runs may need to be rerun
              so full reasoning can be stored.
            </p>
          )}
        </section>
      </article>
    </>
  );
}
