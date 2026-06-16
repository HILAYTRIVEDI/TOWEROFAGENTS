"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { deleteWorkflow } from "@/lib/api";

export function WorkflowRemoveButton({
  workflowId,
  title,
}: {
  workflowId: string;
  title: string;
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [removing, setRemoving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRemove() {
    if (!window.confirm(`Remove workflow "${title}"? This cannot be undone.`)) {
      return;
    }
    setError(null);
    setRemoving(true);
    try {
      await deleteWorkflow(workflowId);
      startTransition(() => router.refresh());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Remove failed.");
    } finally {
      setRemoving(false);
    }
  }

  return (
    <div className="workflow-row-actions">
      <button
        className="button danger"
        disabled={removing || pending}
        onClick={handleRemove}
        type="button"
      >
        {removing || pending ? "Removing…" : "Remove"}
      </button>
      {error ? (
        <p className="notice error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
