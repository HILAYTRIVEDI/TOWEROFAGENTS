import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { ReportReviewPanel } from "@/components/report-review-panel";
import { ApiError, getReport } from "@/lib/api";

export default async function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const result = await getReport(id)
    .then((report) => ({ report, error: null, status: 200 }))
    .catch((error) => ({
      report: null,
      error: error instanceof Error ? error.message : "Report loading failed",
      status: error instanceof ApiError ? error.status : 500,
    }));

  if (!result.report) {
    return (
      <>
        <PageHeader
          eyebrow={`Report ${id}`}
          title="Decision packet"
          description="Agent screening decision, evidence, and recommended next steps."
        />
        <EmptyState
          title={
            result.status === 404
              ? "Report not found"
              : "Report unavailable"
          }
        >
          {result.error}. No successful report is fabricated.
        </EmptyState>
      </>
    );
  }

  const report = result.report;
  const fitScoreDisplay =
    report.fit_score != null
      ? `${Math.round(report.fit_score * 100)}%`
      : "Not scored";
  const bandAudit = report.report_payload?.band_audit;
  const bandModes = Object.entries(bandAudit?.modes ?? {});
  const bandMessageCount = bandAudit?.message_count ?? 0;
  const bandRoom = bandAudit?.room_id ?? "Not configured";

  return (
    <>
      <PageHeader
        eyebrow={`Report ${report.id}`}
        title="Decision packet"
        description="Agent screening decision, evidence, and recommended next steps."
      />

      {report.requires_human_review &&
      report.review_status !== "approved" &&
      report.review_status !== "rejected" ? (
        <p className="notice error" role="alert">
          Human review required — this decision must not be acted upon without a
          qualified reviewer.
        </p>
      ) : null}

      <ReportReviewPanel
        initialStatus={report.review_status}
        requiresHumanReview={report.requires_human_review}
        reviewedAt={report.reviewed_at}
        reviewerNote={report.reviewer_note}
        workflowId={report.workflow_id}
      />

      <section className="detail-grid">
        <article className="detail-card">
          <p className="eyebrow">Recommendation</p>
          <p>
            <span className={`status-badge status-${report.recommendation}`}>
              {report.recommendation.replaceAll("_", " ")}
            </span>
          </p>
          <p style={{ marginTop: "0.75rem" }}>{report.summary}</p>
        </article>

        <article className="detail-card">
          <p className="eyebrow">Fit score</p>
          <p style={{ fontSize: "2rem", fontWeight: 700 }}>{fitScoreDisplay}</p>
          <p className="workflow-row-meta">
            Backed by {report.evidence_chunk_ids.length} retrieved evidence chunk
            {report.evidence_chunk_ids.length === 1 ? "" : "s"}.
          </p>
        </article>
      </section>

      <article className="detail-card">
        <p className="eyebrow">Band audit</p>
        <section className="detail-grid" style={{ marginBottom: 0 }}>
          <div>
            <p style={{ fontSize: "1.35rem", fontWeight: 700 }}>
              {bandMessageCount} message{bandMessageCount === 1 ? "" : "s"}
            </p>
            <p className="workflow-row-meta">Room: {bandRoom}</p>
          </div>
          <div>
            {bandModes.length > 0 ? (
              <ul className="workflow-list">
                {bandModes.map(([mode, count]) => (
                  <li className="workflow-row" key={mode}>
                    <span className={`status-badge status-${mode}`}>{mode}</span>
                    <strong>{count}</strong>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="notice">No Band audit messages were posted for this run.</p>
            )}
            {bandAudit?.error ? (
              <p className="notice error" style={{ marginTop: "0.75rem" }}>
                {bandAudit.error}
              </p>
            ) : null}
          </div>
        </section>
      </article>

      <section className="detail-grid">
        <article className="detail-card">
          <p className="eyebrow">Strengths</p>
          {report.strengths.length > 0 ? (
            <ul className="workflow-list">
              {report.strengths.map((s, i) => (
                <li className="workflow-row" key={i}>
                  {s}
                </li>
              ))}
            </ul>
          ) : (
            <p className="notice">None reported.</p>
          )}
        </article>

        <article className="detail-card">
          <p className="eyebrow">Gaps</p>
          {report.gaps.length > 0 ? (
            <ul className="workflow-list">
              {report.gaps.map((g, i) => (
                <li className="workflow-row" key={i}>
                  {g}
                </li>
              ))}
            </ul>
          ) : (
            <p className="notice">None reported.</p>
          )}
        </article>
      </section>

      <article className="detail-card">
        <p className="eyebrow">Interview questions</p>
        {report.interview_questions.length > 0 ? (
          <ol style={{ paddingLeft: "1.25rem" }}>
            {report.interview_questions.map((q, i) => (
              <li key={i} style={{ marginBottom: "0.5rem" }}>
                {q}
              </li>
            ))}
          </ol>
        ) : (
          <p className="notice">None reported.</p>
        )}
      </article>

      {report.policy_note ? (
        <article className="detail-card">
          <p className="eyebrow">Policy note</p>
          <p>{report.policy_note}</p>
        </article>
      ) : null}
    </>
  );
}
