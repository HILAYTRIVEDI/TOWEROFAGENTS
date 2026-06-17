"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";

import { DocumentUpload } from "@/components/document-upload";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import {
  getWorkflow,
  listDocuments,
  getWorkflowFindings,
  indexWorkflow,
  runWorkflow,
  ApiError,
} from "@/lib/api";
import type { Workflow, DocumentRead, AgentFinding } from "@/lib/types";

export default function WorkflowDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [documents, setDocuments] = useState<DocumentRead[]>([]);
  const [findings, setFindings] = useState<AgentFinding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const [wf, docs, fnds] = await Promise.all([
        getWorkflow(id),
        listDocuments(id).catch(() => []),
        getWorkflowFindings(id).catch(() => []),
      ]);
      setWorkflow(wf);
      setDocuments(docs);
      setFindings(fnds);
      setError(null);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setError("Workflow not found");
      } else {
        setError(err instanceof Error ? err.message : "Failed to load workflow data");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  useEffect(() => {
    if (!workflow) return;

    const isWorkflowActive =
      workflow.status === "indexing" ||
      workflow.status === "running" ||
      documents.some((d) => d.status === "parsing" || d.status === "uploaded");

    if (!isWorkflowActive) return;

    const interval = setInterval(() => {
      fetchData();
    }, 3000);

    return () => clearInterval(interval);
  }, [workflow?.status, documents]);

  const handleIndex = async () => {
    setActionError(null);
    setActionSuccess(null);
    setActionLoading("indexing");
    try {
      const res = await indexWorkflow(id);
      setActionSuccess(res.message || "Indexing started successfully.");
      await fetchData();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to start indexing.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleRun = async () => {
    setActionError(null);
    setActionSuccess(null);
    setActionLoading("running");
    try {
      const res = await runWorkflow(id);
      setActionSuccess(res.message || "Workflow started running.");
      await fetchData();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to start workflow.");
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "grid", placeItems: "center", minHeight: "400px" }}>
        <p className="lede">Loading workflow details...</p>
      </div>
    );
  }

  if (error || !workflow) {
    return (
      <EmptyState title="Workflow Unavailable">
        <p>{error || "Workflow not found."}</p>
        <Link href="/dashboard" className="button">
          Back to Dashboard
        </Link>
      </EmptyState>
    );
  }

  return (
    <>
      <PageHeader
        eyebrow={`Workflow ${workflow.status.replaceAll("_", " ")}`}
        title={workflow.title}
        description={`Template: ${workflow.template_slug ?? "Unassigned"} · Created ${new Date(workflow.created_at).toLocaleString()}`}
        action={
          <div style={{ display: "flex", gap: "12px" }}>
            <button
              className="button"
              onClick={handleIndex}
              disabled={
                actionLoading !== null ||
                workflow.status === "indexing" ||
                workflow.status === "running"
              }
            >
              {actionLoading === "indexing" ? "Indexing..." : "Index Documents"}
            </button>
            <button
              className="button primary"
              onClick={handleRun}
              disabled={
                actionLoading !== null ||
                workflow.status === "indexing" ||
                workflow.status === "running"
              }
            >
              {actionLoading === "running" ? "Running..." : "Run Workflow"}
            </button>
          </div>
        }
      />

      {actionError && (
        <p className="notice error" role="alert" style={{ marginBottom: "24px" }}>
          {actionError}
        </p>
      )}
      {actionSuccess && (
        <p className="notice success" role="status" style={{ marginBottom: "24px" }}>
          {actionSuccess}
        </p>
      )}

      <section className="detail-grid">
        <article className="detail-card">
          <p className="eyebrow">Record</p>
          <dl>
            <div>
              <dt>Workflow ID</dt>
              <dd style={{ fontFamily: "monospace", fontSize: "0.85rem" }}>{workflow.id}</dd>
            </div>
            <div>
              <dt>Organization</dt>
              <dd style={{ fontFamily: "monospace", fontSize: "0.85rem" }}>{workflow.org_id}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <span className={`status-badge status-${workflow.status}`}>
                  {workflow.status.replaceAll("_", " ")}
                </span>
              </dd>
            </div>
            <div>
              <dt>Band room</dt>
              <dd>{workflow.band_room_id ?? "Not assigned"}</dd>
            </div>
          </dl>
        </article>
        <article className="detail-card">
          <DocumentUpload workflowId={workflow.id} onUploadComplete={fetchData} />
        </article>
      </section>

      {/* Document Listing */}
      <section className="detail-card" style={{ marginBottom: "24px" }}>
        <p className="eyebrow">Associated Documents</p>
        <h2>Workflow Files</h2>
        <p className="workflow-row-meta" style={{ marginBottom: "16px" }}>
          Current documents uploaded and their processing/indexing statuses.
        </p>
        {documents.length > 0 ? (
          <ul className="workflow-list">
            {documents.map((doc) => (
              <li className="workflow-row" key={doc.id}>
                <div>
                  <p className="workflow-row-title">{doc.filename}</p>
                  <p className="workflow-row-meta">
                    Type: <span style={{ textTransform: "capitalize", fontWeight: 700 }}>{doc.doc_type || doc.mime_type || "unknown"}</span> · Uploaded {new Date(doc.created_at).toLocaleString()}
                  </p>
                </div>
                <span className={`status-badge status-${doc.status}`}>
                  {doc.status}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="lede" style={{ fontSize: "0.95rem" }}>No documents uploaded yet for this workflow.</p>
        )}
      </section>

      {/* Agent Findings Section */}
      <section className="detail-card" style={{ marginBottom: "24px" }}>
        <p className="eyebrow">Security & Analysis</p>
        <h2>Agent Findings</h2>
        <p className="workflow-row-meta" style={{ marginBottom: "16px" }}>
          Issues, metadata, or key highlights flagged by agents during analysis.
        </p>
        {findings.length > 0 ? (
          <ul className="workflow-list">
            {findings.map((finding, idx) => (
              <li className="workflow-row" key={idx} style={{ flexDirection: "column", alignItems: "stretch", gap: "12px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <h3 style={{ margin: "0 0 4px 0", fontSize: "1.1rem" }}>{finding.title}</h3>
                    <p className="workflow-row-meta">
                      Agent: <strong>{finding.agent_name}</strong> · Type: <strong>{finding.finding_type}</strong>
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <span className={`status-badge`} style={{
                      backgroundColor:
                        finding.severity === "critical" || finding.severity === "high"
                          ? "#f6e3e0"
                          : finding.severity === "medium"
                          ? "#f5ebcf"
                          : "#ebe9df",
                      color:
                        finding.severity === "critical" || finding.severity === "high"
                          ? "var(--red)"
                          : finding.severity === "medium"
                          ? "#7a5b00"
                          : "var(--muted)"
                    }}>
                      {finding.severity}
                    </span>
                    {finding.requires_human_review && (
                      <span className="status-badge status-failed">Review Required</span>
                    )}
                  </div>
                </div>
                <div style={{ fontSize: "0.95rem", whiteSpace: "pre-wrap", color: "var(--muted)", lineHeight: 1.5 }}>
                  {finding.content}
                </div>
                {finding.evidence_chunk_ids && finding.evidence_chunk_ids.length > 0 && (
                  <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                    <strong>Cited Evidence IDs:</strong> {finding.evidence_chunk_ids.join(", ")}
                  </div>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="lede" style={{ fontSize: "0.95rem" }}>No agent findings recorded yet.</p>
        )}
      </section>

      {/* Decision Report Link / Preview */}
      {(workflow.status === "completed" || workflow.status === "awaiting_review") && (
        <EmptyState title="Decision Report Ready">
          <p>
            The workflow has run successfully and a decision packet is ready for your review.
          </p>
          <Link href={`/reports/${workflow.id}`} className="button primary">
            View Decision Report
          </Link>
        </EmptyState>
      )}
    </>
  );
}
