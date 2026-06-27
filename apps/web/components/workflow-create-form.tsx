"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { createWorkflow } from "@/lib/api";

const TEMPLATES = {
  "hr-candidate-screening": {
    label: "HR Candidate Screening",
    artifacts: ["Resume", "Job description", "Hiring policy"],
  },
  "sales-lead-qualification": {
    label: "Sales Lead Qualification",
    artifacts: ["CRM notes"],
  },
  "engineering-change-review": {
    label: "Engineering Change Review",
    artifacts: ["Code diff"],
  },
} as const;

type TemplateSlug = keyof typeof TEMPLATES;

function isTemplateSlug(value: string | undefined): value is TemplateSlug {
  return value !== undefined && value in TEMPLATES;
}

export function WorkflowCreateForm({
  initialTemplate,
  orgId,
}: {
  initialTemplate?: string;
  orgId: string;
}) {
  const router = useRouter();
  const [template, setTemplate] = useState<TemplateSlug>(
    isTemplateSlug(initialTemplate) ? initialTemplate : "hr-candidate-screening",
  );
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    const form = new FormData(event.currentTarget);
    try {
      const workflow = await createWorkflow({
        org_id: orgId,
        title: String(form.get("title") ?? ""),
        user_request: String(form.get("user_request") ?? ""),
        template_slug: template,
        band_room_id: String(form.get("band_room_id") ?? "").trim() || null,
      });
      router.push(`/workflows/${workflow.id}`);
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Workflow creation failed");
      setSubmitting(false);
    }
  }

  return (
    <form className="workflow-form" onSubmit={handleSubmit}>
      {error ? (
        <p className="notice error" role="alert">
          {error}
        </p>
      ) : null}
      <label>
        Workflow template
        <select
          name="template_slug"
          onChange={(event) => setTemplate(event.target.value as TemplateSlug)}
          value={template}
        >
          {Object.entries(TEMPLATES).map(([slug, item]) => (
            <option key={slug} value={slug}>
              {item.label}
            </option>
          ))}
        </select>
      </label>
      <label>
        Workflow title
        <input
          maxLength={200}
          name="title"
          placeholder="Candidate screening: Jane Doe"
          required
          type="text"
        />
      </label>
      <label>
        Review goal
        <textarea
          maxLength={5000}
          name="user_request"
          placeholder="Assess role fit against the supplied job description and hiring policy."
          required
          rows={5}
        />
      </label>
      <label>
        Band room ID
        <input
          maxLength={200}
          name="band_room_id"
          placeholder="Optional separate Band.ai room/session ID"
          type="text"
        />
      </label>
      <fieldset>
        <legend>Required artifacts</legend>
        <div className="artifact-grid">
          {TEMPLATES[template].artifacts.map((item) => (
            <div className="artifact-slot" key={item}>
              <strong>{item}</strong>
              <span>Upload after creating the workflow</span>
            </div>
          ))}
        </div>
      </fieldset>
      <button className="button primary" disabled={submitting} type="submit">
        {submitting ? "Creating…" : "Create workflow"}
      </button>
    </form>
  );
}
