"use client";

import { useState } from "react";

import { uploadOrganizationDocument, uploadWorkflowDocument } from "@/lib/api";
import type { DocumentRead, DocumentType } from "@/lib/types";

// Mirror the server-side cap (MAX_UPLOAD_BYTES default in apps/api/core/config.py)
// so oversized files fail fast in the browser instead of round-tripping a 413.
const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;

const DOC_TYPES: { value: DocumentType; label: string }[] = [
  { value: "resume", label: "Resume" },
  { value: "jd", label: "Job description" },
  { value: "policy", label: "Hiring policy" },
  { value: "crm", label: "CRM notes" },
  { value: "code", label: "Code" },
  { value: "other", label: "Other" },
];

type DocumentUploadProps =
  | {
      scope: "workflow";
      workflowId: string;
      initialDocuments?: DocumentRead[];
    }
  | {
      scope: "organization";
      orgId: string;
      initialDocuments?: DocumentRead[];
    };

export function DocumentUpload(props: DocumentUploadProps) {
  const [docType, setDocType] = useState<DocumentType>("resume");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploaded, setUploaded] = useState<DocumentRead[]>(
    props.initialDocuments ?? [],
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const form = event.currentTarget;
    const input = form.elements.namedItem("file") as HTMLInputElement | null;
    const file = input?.files?.[0];

    if (!file) {
      setError("Choose a file to upload.");
      return;
    }
    if (file.size === 0) {
      setError("That file is empty.");
      return;
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      setError("File exceeds the 25 MiB upload limit.");
      return;
    }

    setUploading(true);
    try {
      const document =
        props.scope === "workflow"
          ? await uploadWorkflowDocument(props.workflowId, file, docType)
          : await uploadOrganizationDocument(props.orgId, file, docType);
      setUploaded((current) => [document, ...current]);
      form.reset();
      setDocType("resume");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <section aria-label="Upload documents">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Documents</p>
          <h2>
            {props.scope === "workflow"
              ? "Upload workflow artifacts"
              : "Upload knowledge documents"}
          </h2>
        </div>
      </div>
      <p className="workflow-row-meta">
        {props.scope === "workflow"
          ? "Files are stored privately for this workflow only."
          : "Files are stored privately at the organization level and can be reused by workflows."}{" "}
        Parsing, chunking, and indexing are not yet wired, so uploads are not
        searchable or used in any run.
      </p>

      <form className="workflow-form" onSubmit={handleSubmit}>
        <label>
          Document type
          <select
            name="doc_type"
            onChange={(event) => setDocType(event.target.value as DocumentType)}
            value={docType}
          >
            {DOC_TYPES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          File
          <input name="file" type="file" />
        </label>

        {error ? (
          <p className="notice error" role="alert">
            {error}
          </p>
        ) : null}

        <button className="button primary" disabled={uploading} type="submit">
          {uploading ? "Uploading…" : "Upload document"}
        </button>
      </form>

      {uploaded.length > 0 ? (
        <ul className="workflow-list">
          {uploaded.map((document) => (
            <li className="workflow-row" key={document.id}>
              <div>
                <p className="workflow-row-title">{document.filename}</p>
                <p className="workflow-row-meta">
                  {document.doc_type} · {document.mime_type ?? "unknown type"}
                </p>
              </div>
              <span className={`status-badge status-${document.status}`}>
                {document.status}
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
