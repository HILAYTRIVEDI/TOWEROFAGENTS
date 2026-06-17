import Link from "next/link";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { ApiError, getWorkflowReport, getReport } from "@/lib/api";

export default async function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  // Try loading by workflow ID first, fallback to report ID if not found
  const result = await getWorkflowReport(id)
    .then((report) => ({ report, error: null, status: 200 }))
    .catch(async () => {
      return getReport(id)
        .then((report) => ({ report, error: null, status: 200 }))
        .catch((error) => ({
          report: null,
          error: error instanceof Error ? error.message : "Report loading failed",
          status: error instanceof ApiError ? error.status : 500,
        }));
    });

  return (
    <>
      <PageHeader
        eyebrow="Report Packet"
        title="Decision Packet"
        description="Comprehensive evaluation including recommendation, strengths, gaps, and evidence-backed citations."
        action={
          <Link href="/dashboard" className="button">
            Back to Dashboard
          </Link>
        }
      />

      {result.report ? (
        <div style={{ display: "grid", gap: "24px" }}>
          
          {/* Recommendation & Overview Section */}
          <section className="detail-grid" style={{ gridTemplateColumns: "1.25fr 1fr" }}>
            <article className="detail-card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
              <div>
                <p className="eyebrow" style={{ color: "var(--green)" }}>Recommendation Summary</p>
                <div style={{ display: "flex", alignItems: "baseline", gap: "12px", marginBottom: "16px" }}>
                  <span className="status-badge" style={{ 
                    fontSize: "1.2rem", 
                    padding: "8px 16px",
                    backgroundColor: result.report.recommendation.toLowerCase().includes("reject") ? "#f6e3e0" : "#e8efdc",
                    color: result.report.recommendation.toLowerCase().includes("reject") ? "var(--red)" : "var(--green-dark)"
                  }}>
                    {result.report.recommendation}
                  </span>
                  {result.report.fit_score !== undefined && result.report.fit_score !== null && (
                    <strong style={{ fontSize: "1.5rem", color: "var(--green-dark)" }}>
                      Fit Score: {result.report.fit_score}%
                    </strong>
                  )}
                </div>
                <p style={{ fontSize: "1.05rem", lineHeight: 1.6, color: "var(--muted)", margin: 0 }}>
                  {result.report.summary}
                </p>
              </div>
            </article>

            <article className="detail-card">
              <p className="eyebrow">Review Flags</p>
              <dl>
                <div>
                  <dt>Human Review Status</dt>
                  <dd style={{ marginTop: "4px" }}>
                    {result.report.requires_human_review ? (
                      <span className="status-badge status-awaiting_review" style={{ fontWeight: 800 }}>
                        ⚠️ Awaiting Human Review
                      </span>
                    ) : (
                      <span className="status-badge status-completed" style={{ fontWeight: 800 }}>
                        ✓ Auto-Approved
                      </span>
                    )}
                  </dd>
                </div>
                <div style={{ marginTop: "12px" }}>
                  <dt>Report ID</dt>
                  <dd style={{ fontFamily: "monospace", fontSize: "0.85rem", color: "var(--muted)" }}>
                    {result.report.id}
                  </dd>
                </div>
                <div style={{ marginTop: "12px" }}>
                  <dt>Workflow ID</dt>
                  <dd style={{ fontFamily: "monospace", fontSize: "0.85rem", color: "var(--muted)" }}>
                    {result.report.workflow_id}
                  </dd>
                </div>
              </dl>
            </article>
          </section>

          {/* Strengths & Gaps */}
          <section className="detail-grid">
            <article className="detail-card" style={{ borderColor: "#cddbb3", backgroundColor: "rgba(232, 239, 220, 0.05)" }}>
              <p className="eyebrow" style={{ color: "var(--green)" }}>Key Strengths</p>
              {result.report.strengths && result.report.strengths.length > 0 ? (
                <ul style={{ margin: 0, paddingLeft: "20px", display: "grid", gap: "12px" }}>
                  {result.report.strengths.map((strength, i) => (
                    <li key={i} style={{ lineHeight: 1.5, color: "var(--green-dark)" }}>
                      {strength}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: "var(--muted)", margin: 0 }}>No specific strengths highlighted.</p>
              )}
            </article>

            <article className="detail-card" style={{ borderColor: "#eec4c0", backgroundColor: "rgba(246, 227, 224, 0.05)" }}>
              <p className="eyebrow" style={{ color: "var(--red)" }}>Identified Gaps</p>
              {result.report.gaps && result.report.gaps.length > 0 ? (
                <ul style={{ margin: 0, paddingLeft: "20px", display: "grid", gap: "12px" }}>
                  {result.report.gaps.map((gap, i) => (
                    <li key={i} style={{ lineHeight: 1.5, color: "#8a241c" }}>
                      {gap}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: "var(--muted)", margin: 0 }}>No significant gaps identified.</p>
              )}
            </article>
          </section>

          {/* Policy Notes */}
          {result.report.policy_note && (
            <section className="detail-card" style={{ borderLeftWidth: "4px", borderLeftColor: "var(--green)" }}>
              <p className="eyebrow">Hiring & Alignment Policy Note</p>
              <div style={{ fontSize: "1rem", lineHeight: 1.6, fontStyle: "italic", color: "var(--ink)" }}>
                "{result.report.policy_note}"
              </div>
            </section>
          )}

          {/* Suggested Interview Questions */}
          <section className="detail-card">
            <p className="eyebrow">Deep Dive</p>
            <h2 style={{ fontSize: "1.4rem", marginBottom: "16px" }}>Suggested Interview Questions</h2>
            {result.report.interview_questions && result.report.interview_questions.length > 0 ? (
              <ol style={{ margin: 0, paddingLeft: "20px", display: "grid", gap: "16px" }}>
                {result.report.interview_questions.map((question, i) => (
                  <li key={i} style={{ lineHeight: 1.5, fontSize: "1rem", color: "var(--ink)", fontWeight: 500 }}>
                    <span style={{ fontWeight: 400, color: "var(--muted)" }}>{question}</span>
                  </li>
                ))}
              </ol>
            ) : (
              <p style={{ color: "var(--muted)", margin: 0 }}>No suggested questions available.</p>
            )}
          </section>

          {/* Cited Evidence */}
          <section className="detail-card">
            <p className="eyebrow">Audit & Evidence</p>
            <h2 style={{ fontSize: "1.4rem", marginBottom: "8px" }}>Cited Evidence Source Chunks</h2>
            <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: "16px" }}>
              These document chunk references were evaluated and synthesized by the verification agent room to produce this decision report.
            </p>
            {result.report.evidence_chunk_ids && result.report.evidence_chunk_ids.length > 0 ? (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                {result.report.evidence_chunk_ids.map((chunkId, idx) => (
                  <span key={idx} style={{ 
                    fontFamily: "monospace", 
                    fontSize: "0.78rem", 
                    padding: "4px 8px", 
                    backgroundColor: "#ebe9df", 
                    color: "var(--muted)", 
                    borderRadius: "6px" 
                  }}>
                    {chunkId}
                  </span>
                ))}
              </div>
            ) : (
              <p style={{ color: "var(--muted)", margin: 0 }}>No cited evidence chunk IDs linked to this report.</p>
            )}
          </section>

        </div>
      ) : (
        <EmptyState title={result.status === 501 ? "Report generation is not implemented" : "Report Unavailable"}>
          <p>{result.error || "The requested decision report does not exist or has not been compiled yet."}</p>
          <div style={{ display: "flex", gap: "12px", marginTop: "16px" }}>
            <Link href={`/workflows/${id}`} className="button">
              Return to Workflow
            </Link>
            <Link href="/dashboard" className="button primary">
              Dashboard
            </Link>
          </div>
        </EmptyState>
      )}
    </>
  );
}
