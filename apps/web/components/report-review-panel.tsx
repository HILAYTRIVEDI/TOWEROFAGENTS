"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError, submitReview } from "@/lib/api";
import type { DecisionPacket, ReviewStatus } from "@/lib/types";

interface Props {
  workflowId: string;
  requiresHumanReview: boolean;
  initialStatus: ReviewStatus | null;
  reviewerNote: string | null;
  reviewedAt: string | null;
  decisionPacket?: DecisionPacket;
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

function DecisionPacketList({
  emptyLabel,
  items,
}: {
  emptyLabel: string;
  items: string[];
}) {
  return items.length > 0 ? (
    <ul className="workflow-list">
      {items.map((item, index) => (
        <li className="workflow-row" key={`${item}-${index}`}>
          {item}
        </li>
      ))}
    </ul>
  ) : (
    <p className="notice">{emptyLabel}</p>
  );
}

function DecisionPacketSection({ packet }: { packet: DecisionPacket }) {
  return (
    <article className="detail-card" style={{ marginBottom: "24px" }}>
      <p className="eyebrow">Decision packet</p>
      <p style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <span className={`status-badge status-${packet.recommendation}`}>
          {packet.recommendation.replaceAll("_", " ")}
        </span>
        {packet.human_approval_required ? (
          <span className="status-badge status-pending_review">
            Human approval required
          </span>
        ) : (
          <span className="status-badge status-approved">
            Human approval not required
          </span>
        )}
      </p>
      <p className="workflow-row-content" style={{ marginTop: "0.75rem" }}>
        {packet.executive_summary}
      </p>
      <section className="detail-grid" style={{ marginTop: "1rem", marginBottom: 0 }}>
        <div>
          <p className="eyebrow">Risks</p>
          <DecisionPacketList emptyLabel="No risks reported." items={packet.risks} />
        </div>
        <div>
          <p className="eyebrow">Missing information</p>
          <DecisionPacketList
            emptyLabel="No missing information reported."
            items={packet.missing_information}
          />
        </div>
        <div>
          <p className="eyebrow">Disagreements</p>
          <DecisionPacketList
            emptyLabel="No disagreements reported."
            items={packet.disagreements}
          />
        </div>
        <div>
          <p className="eyebrow">Next actions</p>
          <DecisionPacketList
            emptyLabel="No next actions reported."
            items={packet.next_actions}
          />
        </div>
      </section>
    </article>
  );
}

export function ReportReviewPanel({
  workflowId,
  requiresHumanReview,
  initialStatus,
  reviewerNote,
  reviewedAt,
  decisionPacket,
}: Props) {
  const router = useRouter();
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Once resolved, the server component re-renders with the persisted state.
  // We derive display from the props coming from the server after refresh.
  const isResolved =
    initialStatus === "approved" || initialStatus === "rejected";

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

  const packetCard = decisionPacket ? (
    <article className="detail-card" style={{ marginBottom: "24px" }}>
      <p className="eyebrow">Vendor decision packet</p>
      <p style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <span className={`status-badge status-${decisionPacket.recommendation}`}>
          {decisionPacket.recommendation.replaceAll("_", " ")}
        </span>
        {decisionPacket.human_approval_required ? (
          <span className="status-badge status-awaiting_review">
            Human approval required
          </span>
        ) : null}
      </p>
      <p className="workflow-row-content" style={{ marginTop: "0.75rem" }}>
        {decisionPacket.executive_summary}
      </p>
      <section className="detail-grid" style={{ marginTop: "1rem", marginBottom: 0 }}>
        <PacketSection title="Risks" values={decisionPacket.risks} />
        <PacketSection
          title="Missing information"
          values={decisionPacket.missing_information}
        />
        <PacketSection
          title="Disagreements"
          values={decisionPacket.disagreements}
        />
        <PacketSection title="Next actions" values={decisionPacket.next_actions} />
      </section>
    </article>
  ) : null;

  if (!requiresHumanReview) {
    return packetCard;
  }

  if (isResolved) {
    return (
      <>
        {packetCard}
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
      </>
    );
  }

  return (
    <>
      {packetCard}
      <article className="detail-card" style={{ marginBottom: "24px" }}>
        <p className="eyebrow">Human review</p>
        <p style={{ marginBottom: "1rem" }}>
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
    </>
  );
}

function PacketSection({
  title,
  values,
}: {
  title: string;
  values: string[];
}) {
  return (
    <div>
      <p className="eyebrow">{title}</p>
      {values.length > 0 ? (
        <ul className="workflow-list">
          {values.map((value, index) => (
            <li className="workflow-row" key={index}>
              {value}
            </li>
          ))}
        </ul>
      ) : (
        <p className="notice">None reported.</p>
      )}
    </div>
  );
}
