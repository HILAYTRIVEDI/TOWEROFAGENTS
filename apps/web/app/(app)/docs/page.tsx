import Link from "next/link";
import type { ReactNode } from "react";

import { PageHeader } from "@/components/page-header";

const quickStartSteps = [
  "Open Workflows and create an HR Candidate Screening draft.",
  "Upload the candidate resume, job description, and hiring policy.",
  "Use the Band room to mention the coordinator and specialists.",
  "Review specialist findings as advisory output before any human decision.",
];

const workflowTypes = [
  {
    name: "HR Candidate Screening",
    status: "Flagship MVP path",
    description:
      "Collects resume, job description, and hiring policy evidence so specialists can compare requirements, check policy, audit bias risk, plan interviews, and summarize advisory findings.",
  },
  {
    name: "Sales Lead Qualification",
    status: "Template scaffold",
    description:
      "Uses supplied ICP, CRM notes, and sales context to reason about lead fit and next-step recommendations without inventing prospect facts.",
  },
  {
    name: "Engineering Change Review",
    status: "Template scaffold",
    description:
      "Uses supplied design notes, code changes, and test evidence to review implementation risk, missing tests, and integration concerns.",
  },
];

const bandAgents = [
  {
    handle: "@hilaytrivedi1224/atower-coordinator",
    role: "Primary room coordinator. Routes work, explains required evidence, and keeps the room honest about current product limits.",
  },
  {
    handle: "@hilaytrivedi1224/atower-rag-retriever",
    role: "Checks evidence availability and retrieval status. It must not invent evidence IDs or citations.",
  },
  {
    handle: "@hilaytrivedi1224/atower-policy-guardian",
    role: "Reviews supplied policy and compliance evidence, then flags conflicts, missing approvals, and escalation needs.",
  },
  {
    handle: "@hilaytrivedi1224/atower-final-decision",
    role: "Synthesizes advisory findings for human review. It does not make autonomous high-impact decisions.",
  },
  {
    handle: "@hilaytrivedi1224/atower-resume-jd-matcher",
    role: "Compares resume evidence against job-description requirements and reports matches, gaps, and uncertainty.",
  },
  {
    handle: "@hilaytrivedi1224/atower-bias-reviewer",
    role: "Audits screening reasoning for unfair assumptions, proxy risks, unsupported inferences, and biased language.",
  },
  {
    handle: "@hilaytrivedi1224/atower-interview-planner",
    role: "Creates fair, job-related interview follow-up questions from evidence gaps.",
  },
  {
    handle: "@hilaytrivedi1224/atower-lead-qualifier",
    role: "Reviews supplied ICP, CRM, and sales-note evidence for lead-fit findings and follow-up recommendations.",
  },
  {
    handle: "@hilaytrivedi1224/atower-engineering-reviewer",
    role: "Reviews supplied engineering changes, design notes, and tests for implementation risk and missing coverage.",
  },
];

const artifactRequirements = [
  {
    workflow: "HR Candidate Screening",
    artifacts: "Candidate resume, job description, hiring policy",
  },
  {
    workflow: "Sales Lead Qualification",
    artifacts: "ICP, CRM notes, prospect context, relevant sales policy",
  },
  {
    workflow: "Engineering Change Review",
    artifacts: "Design notes, code/change summary, test evidence, rollout constraints",
  },
];

const demoPrompts = [
  {
    label: "Coordinator smoke test",
    prompt:
      "@hilaytrivedi1224/atower-coordinator confirm you are connected, summarize the available specialist roster, and state what evidence is required before running HR candidate screening.",
  },
  {
    label: "HR workflow kickoff",
    prompt:
      "@hilaytrivedi1224/atower-coordinator We are preparing an HR Candidate Screening workflow in ATower. The required artifacts are resume, job description, and hiring policy. Please coordinate the available specialists and explain what each agent should review before a human makes any screening decision.",
  },
  {
    label: "Specialist test",
    prompt:
      "@hilaytrivedi1224/atower-resume-jd-matcher confirm you are connected and explain what evidence you need before matching a resume to a job description.",
  },
];

function ManualSection({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="manual-section" id={id}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}

export default function DocsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Help manual"
        title="How to use ATower Of Agents."
        description="A practical operating guide for creating workflows, preparing evidence, using the Band agent room, and understanding current MVP limits."
        action={
          <Link className="button primary" href="/workflows/new">
            Create workflow
          </Link>
        }
      />

      <div className="manual-layout">
        <aside className="manual-toc" aria-label="Docs table of contents">
          <strong>Contents</strong>
          <a href="#quick-start">Quick start</a>
          <a href="#workflows">Workflow types</a>
          <a href="#evidence">Evidence required</a>
          <a href="#band">Band room guide</a>
          <a href="#agents">Agent roster</a>
          <a href="#prompts">Copyable prompts</a>
          <a href="#limits">Current limits</a>
          <a href="#troubleshooting">Troubleshooting</a>
        </aside>

        <div className="manual-content">
          <ManualSection id="quick-start" title="Quick Start">
            <ol className="manual-steps">
              {quickStartSteps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            <p className="manual-note">
              Band agents are infrastructure. Users should not create remote
              agents or handle API keys per workflow. They create workflows,
              upload evidence, and use the configured room.
            </p>
          </ManualSection>

          <ManualSection id="workflows" title="Workflow Types">
            <div className="manual-card-grid">
              {workflowTypes.map((workflow) => (
                <article className="manual-card" key={workflow.name}>
                  <span className="tag">{workflow.status}</span>
                  <h3>{workflow.name}</h3>
                  <p>{workflow.description}</p>
                </article>
              ))}
            </div>
          </ManualSection>

          <ManualSection id="evidence" title="Evidence Required">
            <div className="manual-table" role="table" aria-label="Artifact requirements">
              <div role="row">
                <strong role="columnheader">Workflow</strong>
                <strong role="columnheader">Required artifacts</strong>
              </div>
              {artifactRequirements.map((item) => (
                <div role="row" key={item.workflow}>
                  <span role="cell">{item.workflow}</span>
                  <span role="cell">{item.artifacts}</span>
                </div>
              ))}
            </div>
          </ManualSection>

          <ManualSection id="band" title="Band Room Guide">
            <div className="manual-callout">
              <h3>One-time setup versus daily use</h3>
              <p>
                Admins create the Band remote agents once and store credentials
                in environment variables. End users only create workflow drafts,
                upload artifacts, and mention agents in the configured room.
                Dedicated Band rooms can optionally be automatically provisioned per-workflow.
              </p>
            </div>
            <ol className="manual-steps">
              <li>Open the workflow's dedicated Band room, or the shared default ATower room.</li>
              <li>Confirm the coordinator and specialists are participants.</li>
              <li>Mention agents with their full handle, including the user namespace.</li>
              <li>Never paste credentials, resumes, or private docs into public rooms.</li>
            </ol>
          </ManualSection>

          <ManualSection id="agents" title="Agent Roster">
            <div className="manual-agent-list">
              {bandAgents.map((agent) => (
                <article key={agent.handle}>
                  <code>{agent.handle}</code>
                  <p>{agent.role}</p>
                </article>
              ))}
            </div>
          </ManualSection>

          <ManualSection id="prompts" title="Copyable Prompts">
            <div className="manual-prompt-list">
              {demoPrompts.map((item) => (
                <article className="manual-card" key={item.label}>
                  <h3>{item.label}</h3>
                  <pre>{item.prompt}</pre>
                </article>
              ))}
            </div>
          </ManualSection>

          <ManualSection id="limits" title="Current MVP Limits">
            <ul className="manual-list">
              <li>Agent outputs are advisory and require human review.</li>
              <li>Agents must not invent evidence IDs, citations, scores, or outcomes.</li>
              <li>Missing provider credentials must produce explicit unconfigured behavior.</li>
              <li>Band messages are the visible audit layer, not a substitute for persisted findings.</li>
            </ul>
          </ManualSection>

          <ManualSection id="troubleshooting" title="Troubleshooting">
            <div className="manual-card-grid">
              <article className="manual-card">
                <h3>No agent reply</h3>
                <p>
                  Confirm the agent is a room participant, was mentioned with
                  its full handle, and the <code>band-agent</code> service is running.
                </p>
              </article>
              <article className="manual-card">
                <h3>Provider errors</h3>
                <p>
                  Check <code>LLM_PROVIDER</code>, provider API keys, and that the
                  selected model supports OpenAI tool calling.
                </p>
              </article>
              <article className="manual-card">
                <h3>No workflows listed</h3>
                <p>
                  Set <code>NEXT_PUBLIC_DEFAULT_ORG_ID</code> and confirm the API
                  is reachable at <code>NEXT_PUBLIC_API_BASE_URL</code>.
                </p>
              </article>
            </div>
          </ManualSection>
        </div>
      </div>
    </>
  );
}
