import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { ApiError, getWorkflowReport } from "@/lib/api";

export default async function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const result = await getWorkflowReport(id)
    .then((report) => ({ report, error: null, status: 200 }))
    .catch((error) => ({
      report: null,
      error: error instanceof Error ? error.message : "Report loading failed",
      status: error instanceof ApiError ? error.status : 500,
    }));

  return (
    <>
      <PageHeader
        eyebrow={`Report ${id}`}
        title="Decision packet"
        description="Reports will combine recommendations, evidence, fairness notes, interview questions, and human-review status."
      />
      {result.report ? (
        <section className="detail-card">
          <p className="eyebrow">{result.report.recommendation}</p>
          <h2>{result.report.summary}</h2>
          <p>Human review required: {result.report.requires_human_review ? "Yes" : "No"}</p>
        </section>
      ) : (
        <EmptyState title={result.status === 501 ? "Report generation is not implemented" : "Report unavailable"}>
          {result.error}. No successful report is fabricated.
        </EmptyState>
      )}
    </>
  );
}
