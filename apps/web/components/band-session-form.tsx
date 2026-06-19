"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { setWorkflowBandSession } from "@/lib/api";

export function BandSessionForm({
  currentRoomId,
  workflowId,
}: {
  currentRoomId?: string | null;
  workflowId: string;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<"assign" | "mock" | null>(null);

  async function assignRoom(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting("assign");
    const form = new FormData(event.currentTarget);
    try {
      await setWorkflowBandSession(workflowId, {
        band_room_id: String(form.get("band_room_id") ?? ""),
      });
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Band session update failed");
    } finally {
      setSubmitting(null);
    }
  }

  async function createMockSession() {
    setError(null);
    setSubmitting("mock");
    try {
      await setWorkflowBandSession(workflowId, { create_mock_session: true });
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Band session update failed");
    } finally {
      setSubmitting(null);
    }
  }

  return (
    <section className="band-session-panel">
      {error ? (
        <p className="notice error" role="alert">
          {error}
        </p>
      ) : null}
      <form className="inline-form" onSubmit={assignRoom}>
        <label>
          Separate Band room ID
          <input
            defaultValue={currentRoomId ?? ""}
            maxLength={200}
            name="band_room_id"
            placeholder="Paste Band.ai room/session ID"
            required
            type="text"
          />
        </label>
        <button className="button primary" disabled={submitting !== null} type="submit">
          {submitting === "assign" ? "Saving..." : "Use room"}
        </button>
      </form>
      <button
        className="button"
        disabled={submitting !== null}
        onClick={createMockSession}
        type="button"
      >
        {submitting === "mock" ? "Creating..." : "Create mock session"}
      </button>
    </section>
  );
}
