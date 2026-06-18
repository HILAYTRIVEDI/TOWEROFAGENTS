"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { indexWorkflow, runWorkflow } from "@/lib/api";

export function RunWorkflow({ workflowId }: { workflowId: string }) {
  const router = useRouter();
  const [indexing, setIndexing] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleIndex() {
    setError(null);
    setIndexing(true);
    try {
      await indexWorkflow(workflowId);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Indexing failed.");
    } finally {
      setIndexing(false);
    }
  }

  async function handleRun() {
    setError(null);
    setRunning(true);
    try {
      const result = await runWorkflow(workflowId);
      router.push(`/reports/${result.report_id}`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Run failed.");
      setRunning(false);
    }
  }

  const busy = indexing || running;

  return (
    <section aria-label="Run workflow">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Execution</p>
          <h2>Run screening</h2>
        </div>
      </div>
      <p className="workflow-row-meta">
        Re-index documents first if you have uploaded new files since the last
        run, then start the screening run.
      </p>

      {error ? (
        <p className="notice error" role="alert">
          {error}
        </p>
      ) : null}

      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
        <button
          className="button"
          disabled={busy}
          onClick={() => void handleIndex()}
          type="button"
        >
          {indexing ? "Re-indexing…" : "Re-index documents"}
        </button>
        <button
          className="button primary"
          disabled={busy}
          onClick={() => void handleRun()}
          type="button"
        >
          {running ? "Running…" : "Run screening"}
        </button>
      </div>
    </section>
  );
}
