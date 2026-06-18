import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
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

  return (
    <>
      <PageHeader
        eyebrow={`Report ${report.id}`}
        title="Decision packet"
        description="Agent screening decision, evidence, and recommended next steps."
      />

      {report.requires_human_review ? (
        <p className="notice error" role="alert">
          Human review required — this decision must not be acted upon without a
          qualified reviewer.
        </p>
      ) : null}

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
