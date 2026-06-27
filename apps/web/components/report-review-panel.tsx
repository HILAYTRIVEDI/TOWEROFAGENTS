"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError, submitReview } from "@/lib/api";
import type { ReviewStatus } from "@/lib/types";

interface Props {
  workflowId: string;
  requiresHumanReview: boolean;
  initialStatus: ReviewStatus | null;
  reviewerNote: string | null;
  reviewedAt: string | null;
}

function reviewErrorMessage(cause: unknown): string {
  if (cause instanceof ApiError) {
    if (cause.status === 409) {
      return "Review already submitted for this report. Refresh to see the current status.";
    }
    if (cause.status === 400) {
      return cause.message || "This report does not require human review.";
    }
    if (cause.status === 404) {
      return cause.message || "Report not found — cannot submit review.";
    }
    return cause.message;
  }
  return cause instanceof Error ? cause.message : "Review submission failed.";
}

export function ReportReviewPanel({
  workflowId,
  requiresHumanReview,
  initialStatus,
  reviewerNote,
  reviewedAt,
}: Props) {
  const router = useRouter();
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Once resolved, the server component re-renders with the persisted state.
  // We derive display from the props coming from the server after refresh.
  const isResolved =
    initialStatus === "approved" || initialStatus === "rejected";

  if (!requiresHumanReview) {
    return null;
  }

  async function handleDecision(decision: "approve" | "reject") {
    setError(null);
    setSubmitting(true);
    try {
      await submitReview(workflowId, decision, note.trim() || undefined);
      router.refresh();
    } catch (cause) {
      setError(reviewErrorMessage(cause));
      setSubmitting(false);
    }
  }

  if (isResolved) {
    return (
      <article className="detail-card" style={{ marginBottom: "24px" }}>
        <p className="eyebrow">Human review</p>
        <p>
          <span
            className={`status-badge status-${initialStatus}`}
            role="status"
          >
            {initialStatus === "approved" ? "Approved" : "Rejected"}
          </span>
        </p>
        {reviewerNote ? (
          <p className="workflow-row-content" style={{ marginTop: "0.75rem" }}>
            {reviewerNote}
          </p>
        ) : null}
        {reviewedAt ? (
          <p className="workflow-row-meta" style={{ marginTop: "0.5rem" }}>
            Reviewed {new Date(reviewedAt).toLocaleString()}
          </p>
        ) : null}
      </article>
    );
  }

  return (
    <article className="detail-card" style={{ marginBottom: "24px" }}>
      <p className="eyebrow">Human review</p>
      <p className="workflow-row-meta" style={{ marginBottom: "1rem" }}>
        This report requires a qualified reviewer before any action is taken.
      </p>

      {error ? (
        <p className="notice error" role="alert" style={{ marginBottom: "1rem" }}>
          {error}
        </p>
      ) : null}

      <label
        style={{
          display: "grid",
          gap: "8px",
          color: "var(--green-dark)",
          fontWeight: 750,
          marginBottom: "1rem",
        }}
      >
        Note (optional, max 2000 characters)
        <textarea
          disabled={submitting}
          maxLength={2000}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Add a reviewer note…"
          rows={3}
          style={{
            width: "100%",
            padding: "10px 12px",
            background: "white",
            border: "1px solid var(--line)",
            borderRadius: "8px",
            fontWeight: 400,
            resize: "vertical",
          }}
          value={note}
        />
      </label>

      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
        <button
          className="button primary"
          disabled={submitting}
          onClick={() => void handleDecision("approve")}
          type="button"
        >
          {submitting ? "Submitting…" : "Approve"}
        </button>
        <button
          className="button danger"
          disabled={submitting}
          onClick={() => void handleDecision("reject")}
          type="button"
        >
          {submitting ? "Submitting…" : "Reject"}
        </button>
      </div>
    </article>
  );
}
