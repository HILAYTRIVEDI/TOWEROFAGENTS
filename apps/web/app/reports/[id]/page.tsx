import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";

export default async function ReportPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ state?: string }>;
}) {
  const [{ id }, { state }] = await Promise.all([params, searchParams]);

  if (state === "loading") {
    return (
      <p className="notice" role="status">
        Loading report…
      </p>
    );
  }

  if (state === "error") {
    return (
      <p className="notice error" role="alert">
        The report could not be loaded.
      </p>
    );
  }

  return (
    <>
      <PageHeader
        eyebrow={`Report ${id}`}
        title="Decision packet"
        description="Reports will combine recommendations, evidence, fairness notes, interview questions, and human-review status."
      />
      <EmptyState title="Report not generated">
        This route handles loading and error states without fabricating a
        successful report. Report generation belongs to the product phase.
      </EmptyState>
    </>
  );
}

