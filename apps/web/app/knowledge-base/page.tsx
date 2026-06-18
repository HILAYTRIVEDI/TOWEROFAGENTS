import { DocumentUpload } from "@/components/document-upload";
import { PageHeader } from "@/components/page-header";
import { listOrganizationDocuments } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function KnowledgeBasePage() {
  const orgId = process.env.NEXT_PUBLIC_DEFAULT_ORG_ID;
  let error: string | null = null;
  const documents = orgId
    ? await listOrganizationDocuments(orgId).catch((caught) => {
        error = caught instanceof Error ? caught.message : "Knowledge loading failed";
        return [];
      })
    : [];

  return (
    <>
      <PageHeader
        eyebrow="Knowledge base"
        title="Upload once. Reuse everywhere."
        description="Organization-scoped documents live in private Supabase storage and are available for future workflow indexing."
      />
      {!orgId ? (
        <p className="notice error" role="alert">
          Set NEXT_PUBLIC_DEFAULT_ORG_ID to load organization knowledge.
        </p>
      ) : null}
      {error ? (
        <p className="notice error" role="alert">
          {error}
        </p>
      ) : null}
      {orgId ? (
        <DocumentUpload
          initialDocuments={documents}
          orgId={orgId}
          scope="organization"
        />
      ) : null}
    </>
  );
}
