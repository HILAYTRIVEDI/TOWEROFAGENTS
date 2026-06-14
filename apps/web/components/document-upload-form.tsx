"use client";

import { useState } from "react";

import { uploadDocument } from "@/lib/api";

const DOCUMENT_TYPES = [
  ["resume", "Resume"],
  ["jd", "Job description"],
  ["policy", "Policy"],
  ["crm", "CRM notes"],
  ["code", "Code or diff"],
  ["other", "Other"],
] as const;

export function DocumentUploadForm({ workflowId }: { workflowId: string }) {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setUploading(true);

    const form = new FormData(event.currentTarget);
    const file = form.get("file");
    if (!(file instanceof File) || file.size === 0) {
      setError("Choose a file to upload.");
      setUploading(false);
      return;
    }

    try {
      const document = await uploadDocument(
        workflowId,
        String(form.get("doc_type") ?? "other"),
        file,
      );
      setMessage(`${document.filename} uploaded with status “${document.status}”.`);
      event.currentTarget.reset();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <label>
        Artifact type
        <select defaultValue="resume" name="doc_type">
          {DOCUMENT_TYPES.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <label>
        File
        <input name="file" required type="file" />
      </label>
      <button className="button primary" disabled={uploading} type="submit">
        {uploading ? "Uploading…" : "Upload artifact"}
      </button>
      {message ? (
        <p className="notice success" role="status">
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="notice error" role="alert">
          {error}
        </p>
      ) : null}
    </form>
  );
}
