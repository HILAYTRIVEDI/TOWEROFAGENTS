"use client";

import { useState } from "react";

import {
  deleteOrganizationDocument,
  deleteWorkflowDocument,
  uploadOrganizationDocument,
  uploadWorkflowDocument,
} from "@/lib/api";
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
  { value: "vendor_profile", label: "Vendor profile" },
  { value: "contract", label: "Contract" },
  { value: "security_documentation", label: "Security documentation" },
  { value: "pricing", label: "Pricing" },
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
  const [activeType, setActiveType] = useState<DocumentType | "all">("all");
  const [uploading, setUploading] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploaded, setUploaded] = useState<DocumentRead[]>(
    props.initialDocuments ?? [],
  );
  const visibleDocuments =
    activeType === "all"
      ? uploaded
      : uploaded.filter((document) => document.doc_type === activeType);

  function countFor(type: DocumentType | "all"): number {
    return type === "all"
      ? uploaded.length
      : uploaded.filter((document) => document.doc_type === type).length;
  }

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

  async function handleRemove(document: DocumentRead) {
    setError(null);
    setRemovingId(document.id);
    try {
      if (props.scope === "workflow") {
        await deleteWorkflowDocument(props.workflowId, document.id);
      } else {
        await deleteOrganizationDocument(props.orgId, document.id);
      }
      setUploaded((current) => current.filter((item) => item.id !== document.id));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Remove failed.");
    } finally {
      setRemovingId(null);
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
        Documents are indexed for retrieval and used during workflow runs.
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
        <section className="document-history">
          <div aria-label="Document history tabs" className="tab-list" role="tablist">
            {[{ value: "all" as const, label: "All" }, ...DOC_TYPES].map((option) => (
              <button
                aria-selected={activeType === option.value}
                className={`tab-trigger ${activeType === option.value ? "active" : ""}`}
                key={option.value}
                onClick={() => setActiveType(option.value)}
                role="tab"
                type="button"
              >
                {option.label} ({countFor(option.value)})
              </button>
            ))}
          </div>
          {visibleDocuments.length > 0 ? (
            <ul className="workflow-list">
              {visibleDocuments.map((document) => (
                <li className="workflow-row" key={document.id}>
                  <div className="workflow-row-main">
                    <p className="workflow-row-title">{document.filename}</p>
                    <p className="workflow-row-meta">
                      {document.doc_type} · {document.mime_type ?? "unknown type"} ·{" "}
                      {new Date(document.created_at).toLocaleString()} ·{" "}
                      {document.workflow_id ? "Workflow file" : "Shared knowledge"}
                    </p>
                  </div>
                  <div className="workflow-row-trailing">
                    <span className={`status-badge status-${document.status}`}>
                      {document.status}
                    </span>
                    <button
                      className="button danger"
                      disabled={removingId === document.id}
                      onClick={() => void handleRemove(document)}
                      type="button"
                    >
                      {removingId === document.id ? "Removing..." : "Remove"}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="notice">No documents in this tab.</p>
          )}
        </section>
      ) : (
        <p className="notice">No documents uploaded yet.</p>
      )}
    </section>
  );
}
