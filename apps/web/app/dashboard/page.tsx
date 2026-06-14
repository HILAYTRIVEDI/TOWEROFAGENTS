import Link from "next/link";

import { PageHeader } from "@/components/page-header";

const TEMPLATES = [
  {
    name: "HR Candidate Screening",
    depth: "Deep workflow",
    description: "Resume, role, and policy review with fairness and evidence gates.",
    ready: true,
  },
  {
    name: "Sales Lead Qualification",
    depth: "Breadth template",
    description: "ICP fit, pain points, outreach, and a next action.",
    ready: false,
  },
  {
    name: "Engineering Change Review",
    depth: "Breadth template",
    description: "Risk, bugs, tests, and a ship-or-block recommendation.",
    ready: false,
  },
] as const;

export default function DashboardPage() {
  return (
    <>
      <PageHeader
        eyebrow="Control tower"
        title="Build decisions you can inspect."
        description="Create a workflow, ground agents in company evidence, and follow their collaboration from intake to human review."
        action={
          <Link className="button primary" href="/workflows/new">
            New workflow
          </Link>
        }
      />

      <section className="metric-grid" aria-label="System readiness">
        <article className="metric-card">
          <span>API</span>
          <strong>Scaffolded</strong>
          <small>Health and typed contracts</small>
        </article>
        <article className="metric-card">
          <span>Data</span>
          <strong>Mapped</strong>
          <small>Supabase + pgvector schema</small>
        </article>
        <article className="metric-card">
          <span>Runtime</span>
          <strong>Mock mode</strong>
          <small>No external calls by default</small>
        </article>
      </section>

      <section>
        <div className="section-heading">
          <div>
            <p className="eyebrow">Workflow library</p>
            <h2>Start from a focused team</h2>
          </div>
          <Link href="/workflows">View workflows</Link>
        </div>
        <div className="template-grid">
          {TEMPLATES.map((template, index) => (
            <article className="template-card" key={template.name}>
              <span className="template-index">0{index + 1}</span>
              <p className="tag">{template.depth}</p>
              <h3>{template.name}</h3>
              <p>{template.description}</p>
              {template.ready ? (
                <Link href="/workflows/new">Configure workflow</Link>
              ) : (
                <span className="muted-link">Planned for product phase</span>
              )}
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

