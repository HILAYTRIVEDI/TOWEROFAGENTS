import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";

export default function KnowledgeBasePage() {
  return (
    <>
      <PageHeader
        eyebrow="Knowledge base"
        title="Evidence before opinion."
        description="Artifacts will be parsed, chunked, embedded, and scoped to their organization and workflow."
      />
      <EmptyState title="No indexed artifacts">
        Storage and indexing are intentionally left for the product phase. The
        parser, chunker, retrieval contract, and vector schema are ready.
      </EmptyState>
    </>
  );
}

