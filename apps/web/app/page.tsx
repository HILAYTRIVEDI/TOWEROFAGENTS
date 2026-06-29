import Link from "next/link";

import FaqAccordion from "@/components/landing/FaqAccordion";

// Server component — no client JS needed for this page except the FaqAccordion (which uses native <details>).

export default function HomePage() {
  return (
    <>
      {/* ── NAVBAR ─────────────────────────────────────────────────── */}
      <header className="lp-nav-wrap" role="banner">
        <nav className="lp-nav" aria-label="Main navigation">
          <Link href="/" className="lp-logo" aria-label="Tower of Agents home">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true">
              <rect width="28" height="28" rx="6" fill="var(--green-dark)" />
              <rect x="8" y="8" width="5" height="5" rx="1" fill="var(--lime)" />
              <rect x="15" y="8" width="5" height="5" rx="1" fill="var(--lime)" opacity="0.6" />
              <rect x="8" y="15" width="5" height="5" rx="1" fill="var(--lime)" opacity="0.6" />
              <rect x="15" y="15" width="5" height="5" rx="1" fill="var(--lime)" />
            </svg>
            <span>Tower of Agents</span>
          </Link>
          <ul className="lp-nav-links" role="list">
            <li><a href="#product">Product</a></li>
            <li><a href="#use-cases">Use Cases</a></li>
            <li><a href="#how-it-works">How It Works</a></li>
            <li><a href="#security">Security</a></li>
            <li><a href="#pricing">Pricing</a></li>
          </ul>
          <a
            href="mailto:hilaytrivedi1224@gmail.com?subject=Tower%20of%20Agents%20Demo"
            className="lp-btn-primary"
          >
            Book a Demo
          </a>
        </nav>
      </header>

      <main id="main-content">
        {/* ── HERO ───────────────────────────────────────────────────── */}
        <section className="lp-hero" aria-labelledby="hero-heading">
          <div className="lp-container lp-hero-inner">
            <div className="lp-hero-copy">
              <p className="eyebrow">AI Control Tower</p>
              <h1 id="hero-heading">The AI Control Tower for Enterprise Workflows</h1>
              <p className="lp-hero-sub">
                Tower of Agents helps companies run document-heavy internal workflows using
                role-based AI agents, evidence-backed decision packets, and human approval.
              </p>
              <p className="lp-hero-support">
                Start with vendor onboarding, procurement review, HR screening, policy
                checks, and compliance-heavy approvals.
              </p>
              <div className="lp-hero-ctas">
                <a
                  href="mailto:hilaytrivedi1224@gmail.com?subject=Tower%20of%20Agents%20Demo"
                  className="lp-btn-primary"
                >
                  Book a Demo
                </a>
                <a href="#decision-packet" className="lp-btn-ghost">
                  View Sample Decision Packet
                </a>
              </div>
              <ul className="lp-trust-chips" role="list" aria-label="Trust attributes">
                {[
                  "Evidence-backed",
                  "Human-in-the-loop",
                  "Audit-ready",
                  "BYOM-ready",
                  "Self-hosted roadmap",
                ].map((chip) => (
                  <li key={chip} className="lp-trust-chip">
                    <span aria-hidden="true" className="lp-chip-dot" />
                    {chip}
                  </li>
                ))}
              </ul>
            </div>

            {/* Hero Visual */}
            <div className="lp-hero-visual" aria-label="Decision packet preview and agent pipeline">
              {/* Decision Packet Card */}
              <div className="lp-dp-card">
                <div className="lp-dp-card-header">
                  <span className="lp-dp-badge lp-dp-badge--amber">Human Approval Required</span>
                  <span className="lp-dp-vendor">Vendor Onboarding Review</span>
                </div>
                <div className="lp-dp-row">
                  <span className="lp-dp-label">Recommendation</span>
                  <span className="lp-dp-val lp-dp-val--amber">Conditional Approval</span>
                </div>
                <div className="lp-dp-row">
                  <span className="lp-dp-label">Key Risk</span>
                  <span className="lp-dp-val lp-dp-val--red">Missing SOC 2</span>
                </div>
                <div className="lp-dp-row">
                  <span className="lp-dp-label">Approval Required</span>
                  <span className="lp-dp-val">Yes</span>
                </div>
                <div className="lp-dp-row">
                  <span className="lp-dp-label">Time Saved</span>
                  <span className="lp-dp-val lp-dp-val--green">3.5 hours</span>
                </div>
                <div className="lp-dp-row">
                  <span className="lp-dp-label">Evidence Sources</span>
                  <span className="lp-dp-val">7 cited</span>
                </div>
              </div>

              {/* Agent Pipeline */}
              <div className="lp-pipeline" aria-label="Agent pipeline steps">
                <div className="lp-pipeline-label">Vendor Onboarding Workflow</div>
                <div className="lp-pipeline-steps">
                  {["Procurement", "Legal", "Security", "Finance", "Compliance", "Controller"].map(
                    (step, i) => (
                      <div key={step} className="lp-pipeline-step-wrap">
                        <div className="lp-pipeline-step">{step}</div>
                        {i < 5 && (
                          <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" className="lp-pipeline-arrow">
                            <path d="M3 8h10M9 4l4 4-4 4" stroke="var(--green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                          </svg>
                        )}
                      </div>
                    )
                  )}
                </div>
                <div className="lp-pipeline-output">
                  <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
                    <path d="M7 2v10M3 8l4 4 4-4" stroke="var(--green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                  </svg>
                  Decision Packet → Human Approval
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── PROBLEM ────────────────────────────────────────────────── */}
        <section className="lp-section lp-section--alt" id="problem" aria-labelledby="problem-heading">
          <div className="lp-container">
            <p className="eyebrow">The Problem</p>
            <h2 id="problem-heading">Enterprise work is stuck between documents, tools, and human memory.</h2>
            <p className="lp-section-sub">
              Companies make critical decisions daily across procurement, HR, finance, legal,
              security, sales, and engineering — but the evidence is scattered across PDFs, Slack,
              email, spreadsheets, CRMs, ERPs, HRMs, Jira, GitHub, and internal policies. Each
              review cycle depends on individual memory, tribal knowledge, and error-prone
              copy-paste.
            </p>
            <div className="lp-cards lp-cards--2">
              <div className="lp-card">
                <div className="lp-card-icon lp-card-icon--red" aria-hidden="true">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5" />
                    <path d="M12 7v5l3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                </div>
                <h3>Manual review is slow</h3>
                <p>A single vendor onboarding review touches 4–6 people over 2–5 days. Documents pile up. Reviewers context-switch. Deadlines slip.</p>
              </div>
              <div className="lp-card">
                <div className="lp-card-icon lp-card-icon--red" aria-hidden="true">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                </div>
                <h3>Decisions are inconsistent</h3>
                <p>The same vendor reviewed by two analysts produces different outcomes. No shared rubric, no memory of past decisions, no enforceable standard.</p>
              </div>
              <div className="lp-card">
                <div className="lp-card-icon lp-card-icon--red" aria-hidden="true">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <h3>AI outputs are hard to trust</h3>
                <p>Generic chatbots hallucinate facts, omit critical risks, and provide no audit trail. Legal and compliance teams cannot act on unverified AI answers.</p>
              </div>
              <div className="lp-card">
                <div className="lp-card-icon lp-card-icon--red" aria-hidden="true">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="1.5" />
                    <path d="M3 9h18M9 21V9" stroke="currentColor" strokeWidth="1.5" />
                  </svg>
                </div>
                <h3>Workflows are invisible</h3>
                <p>Work happens in email threads and chat. There is no single place to see what is in review, who is blocked, what was decided, or why.</p>
              </div>
            </div>
          </div>
        </section>

        {/* ── SOLUTION ───────────────────────────────────────────────── */}
        <section className="lp-section" id="solution" aria-labelledby="solution-heading">
          <div className="lp-container">
            <p className="eyebrow">The Solution</p>
            <h2 id="solution-heading">TOA turns internal requests into auditable decision packets.</h2>
            <p className="lp-section-sub">
              Instead of one generic chatbot, Tower of Agents creates a role-based AI review team
              for each workflow.
            </p>
            <div className="lp-cards lp-cards--3">
              <div className="lp-card lp-card--accent">
                <div className="lp-card-icon" aria-hidden="true">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <h3>Company Brain</h3>
                <p>Upload your internal policies, pricing thresholds, compliance rules, approved vendor lists, and past decisions. Agents review against your standards — not generic training data.</p>
              </div>
              <div className="lp-card lp-card--accent">
                <div className="lp-card-icon" aria-hidden="true">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <circle cx="9" cy="7" r="4" stroke="currentColor" strokeWidth="1.5" />
                    <path d="M3 21v-2a4 4 0 014-4h4a4 4 0 014 4v2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                    <circle cx="19" cy="7" r="2" stroke="currentColor" strokeWidth="1.5" />
                    <path d="M23 21v-1a4 4 0 00-3-3.87" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                </div>
                <h3>Agent Workforce</h3>
                <p>Specialist agents — Procurement, Finance, Legal, Security, Compliance, Controller — each review from their domain perspective, cite evidence, flag risks, and record their finding.</p>
              </div>
              <div className="lp-card lp-card--accent">
                <div className="lp-card-icon" aria-hidden="true">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" stroke="currentColor" strokeWidth="1.5" />
                  </svg>
                </div>
                <h3>Decision Packet</h3>
                <p>Every workflow produces a structured packet: recommendation, executive summary, evidence citations, risk flags, agent findings, next actions, and a human approval step. Nothing leaves without a paper trail.</p>
              </div>
            </div>
          </div>
        </section>

        {/* ── MAIN USE CASE ──────────────────────────────────────────── */}
        <section className="lp-section lp-section--alt" id="product" aria-labelledby="usecase-heading">
          <div className="lp-container">
            <p className="eyebrow">Main Use Case</p>
            <h2 id="usecase-heading">Start with vendor onboarding and procurement review.</h2>
            <p className="lp-section-sub">
              The most common, highest-value entry point for enterprise AI automation.
            </p>

            {/* Workflow Strip */}
            <div className="lp-workflow-strip" role="list" aria-label="Workflow steps">
              {[
                "Upload vendor documents",
                "Agents review evidence",
                "Risks flagged",
                "Decision packet generated",
                "Human approves",
              ].map((step, i) => (
                <div key={step} className="lp-workflow-step-wrap" role="listitem">
                  <div className="lp-workflow-step">
                    <span className="lp-workflow-num">{i + 1}</span>
                    {step}
                  </div>
                  {i < 4 && (
                    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" className="lp-workflow-arrow">
                      <path d="M4 10h12M12 6l4 4-4 4" stroke="var(--green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                    </svg>
                  )}
                </div>
              ))}
            </div>

            {/* Review Areas */}
            <h3 className="lp-sub-heading">What each specialist agent reviews</h3>
            <div className="lp-cards lp-cards--3">
              {[
                { role: "Procurement", desc: "Pricing competitiveness, contract terms, approved vendor status, renewal risk." },
                { role: "Finance", desc: "Payment terms, budget alignment, currency risk, invoice history." },
                { role: "Legal", desc: "Liability clauses, auto-renewal terms, IP ownership, data processing agreements." },
                { role: "Security", desc: "SOC 2 certification, penetration test results, data handling, breach history." },
                { role: "Compliance", desc: "Regulatory alignment (GDPR, CCPA, HIPAA), policy exceptions, audit requirements." },
                { role: "Controller", desc: "Final cross-agent synthesis: summarizes disagreements, surfaces gaps, issues recommendation." },
              ].map(({ role, desc }) => (
                <div key={role} className="lp-card">
                  <h4 className="lp-role-title">{role}</h4>
                  <p>{desc}</p>
                </div>
              ))}
            </div>

            {/* Example Output */}
            <div className="lp-example-output" aria-label="Example decision packet output">
              <div className="lp-example-header">
                <span className="eyebrow">Example Output</span>
                <span className="lp-dp-badge lp-dp-badge--amber">Human Approval Required</span>
              </div>
              <div className="lp-example-grid">
                <div>
                  <span className="lp-dp-label">Recommendation</span>
                  <span className="lp-dp-val lp-dp-val--amber">Conditional Approval</span>
                </div>
                <div>
                  <span className="lp-dp-label">Key Risk</span>
                  <span className="lp-dp-val lp-dp-val--red">SOC 2 report missing</span>
                </div>
                <div>
                  <span className="lp-dp-label">Evidence</span>
                  <span className="lp-dp-val">7 cited sources</span>
                </div>
              </div>
              <div className="lp-example-actions">
                <p className="lp-dp-label" style={{ marginBottom: "0.5rem" }}>Next Actions</p>
                <ol className="lp-action-list">
                  <li>Request SOC 2 report from vendor</li>
                  <li>Send auto-renewal clause to legal for review</li>
                  <li>Re-run review after missing documents are added</li>
                </ol>
              </div>
              <p className="lp-example-approval"><strong>Human Approval:</strong> Required before onboarding proceeds.</p>
            </div>

            <div className="lp-section-cta">
              <a href="#decision-packet" className="lp-btn-secondary">See Sample Vendor Review</a>
            </div>
          </div>
        </section>

        {/* ── HOW IT WORKS ───────────────────────────────────────────── */}
        <section className="lp-section" id="how-it-works" aria-labelledby="how-heading">
          <div className="lp-container">
            <p className="eyebrow">How It Works</p>
            <h2 id="how-heading">Five steps from request to approved decision.</h2>
            <ol className="lp-steps" role="list">
              {[
                {
                  title: "Connect your context",
                  desc: "Upload your internal policies, approved vendor lists, compliance rules, pricing guidelines, and historical decisions into the Company Brain. Agents review against your standards.",
                },
                {
                  title: "Choose a workflow",
                  desc: "Select a workflow template — Vendor Onboarding, HR Screening, Contract Review, Policy Exception — or configure a custom one. Upload the documents for this request.",
                },
                {
                  title: "Run specialist agents",
                  desc: "TOA dispatches role-based agents in parallel. Each agent reads the evidence, checks it against your Company Brain, flags risks, cites sources, and records a finding.",
                },
                {
                  title: "Generate the decision packet",
                  desc: "A Controller agent synthesizes all findings into a structured packet: recommendation, executive summary, risk flags, evidence citations, agent disagreements, missing information, and next actions.",
                },
                {
                  title: "Approve, override, or improve",
                  desc: "A human reviewer sees the full packet, approves or overrides with a note, and the decision is logged. Every override trains the eval flywheel — your agents improve over time.",
                },
              ].map(({ title, desc }, i) => (
                <li key={title} className="lp-step">
                  <div className="lp-step-num" aria-hidden="true">{i + 1}</div>
                  <div className="lp-step-body">
                    <h3>{title}</h3>
                    <p>{desc}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* ── PRODUCT MODULES ────────────────────────────────────────── */}
        <section className="lp-section lp-section--alt" aria-labelledby="modules-heading">
          <div className="lp-container">
            <p className="eyebrow">Product Modules</p>
            <h2 id="modules-heading">Everything enterprises need to deploy agents safely.</h2>
            <div className="lp-cards lp-cards--3">
              {[
                {
                  icon: "M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18",
                  title: "Model Harness",
                  desc: "Route each agent to the best model for its task. Mix providers, control costs, enforce compliance requirements. BYOM-ready from day one.",
                },
                {
                  icon: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
                  title: "Sandbox",
                  desc: "Test new workflows, prompts, and model configurations against real data without affecting production decisions. Ship changes with confidence.",
                },
                {
                  icon: "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
                  title: "Company Brain",
                  desc: "Your internal policies, approved lists, pricing thresholds, and compliance rules — stored as retrievable context so agents always review against your standards.",
                },
                {
                  icon: "M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z M13 2v7h7",
                  title: "Eval Flywheel",
                  desc: "Every human approval, override, and correction feeds back into the evaluation system. Agents improve with every workflow run. Quality compounds over time.",
                },
                {
                  icon: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z",
                  title: "Human Approval",
                  desc: "A structured review interface shows the full decision packet, agent findings, and evidence citations. Approvers confirm, override, or request more information — with full audit logging.",
                },
                {
                  icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01",
                  title: "Audit Trail",
                  desc: "Every agent run, document version, finding, override, and approval is timestamped and stored. Compliance teams get a complete, exportable decision history.",
                },
              ].map(({ icon, title, desc }) => (
                <div key={title} className="lp-card">
                  <div className="lp-card-icon" aria-hidden="true">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path d={icon} stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>
                  <h3>{title}</h3>
                  <p>{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── DECISION PACKET ────────────────────────────────────────── */}
        <section className="lp-section" id="decision-packet" aria-labelledby="dp-heading">
          <div className="lp-container">
            <p className="eyebrow">Decision Packet</p>
            <h2 id="dp-heading">Not chatbot answers. Audit-ready decision packets.</h2>
            <p className="lp-section-sub">
              Every workflow produces a structured packet that a human can review, approve, and
              store — not a chat thread that disappears.
            </p>

            <div className="lp-dp-layout">
              {/* What every packet includes */}
              <div>
                <h3 className="lp-sub-heading">Every packet includes</h3>
                <ul className="lp-checklist" aria-label="Decision packet contents">
                  {[
                    "Recommendation",
                    "Executive summary",
                    "Evidence citations",
                    "Agent findings (per role)",
                    "Risk flags",
                    "Missing information",
                    "Disagreements between agents",
                    "Confidence score",
                    "Next actions",
                    "Human approval status",
                    "Full audit trail",
                  ].map((item) => (
                    <li key={item}>
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                        <path d="M3 8l3 3 7-7" stroke="var(--green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Rich example packet */}
              <div className="lp-dp-example">
                <div className="lp-dp-example-header">
                  <div>
                    <div className="lp-dp-example-title">Acme Analytics</div>
                    <div className="lp-dp-example-wf">Vendor Onboarding Review</div>
                  </div>
                  <span className="lp-dp-badge lp-dp-badge--amber">Human Approval Required</span>
                </div>

                <div className="lp-dp-rec">
                  <span className="lp-dp-label">Recommendation</span>
                  <span className="lp-dp-val lp-dp-val--amber">Conditional Approval</span>
                </div>

                <div className="lp-dp-risks">
                  <p className="lp-dp-label">Risks</p>
                  <ul>
                    <li className="lp-risk lp-risk--red">SOC 2 certification missing</li>
                    <li className="lp-risk lp-risk--amber">Auto-renewal clause requires legal review</li>
                    <li className="lp-risk lp-risk--amber">Customer data processing scope unclear</li>
                  </ul>
                </div>

                <div className="lp-dp-findings">
                  <p className="lp-dp-label">Agent Findings</p>
                  <ul>
                    <li className="lp-finding lp-finding--green">
                      <span className="lp-finding-role">Procurement</span>
                      <span className="lp-finding-status">Approved</span>
                    </li>
                    <li className="lp-finding lp-finding--amber">
                      <span className="lp-finding-role">Finance</span>
                      <span className="lp-finding-status">Approved with budget note</span>
                    </li>
                    <li className="lp-finding lp-finding--red">
                      <span className="lp-finding-role">Security</span>
                      <span className="lp-finding-status">Blocked — SOC 2 required</span>
                    </li>
                    <li className="lp-finding lp-finding--amber">
                      <span className="lp-finding-role">Legal</span>
                      <span className="lp-finding-status">Needs review</span>
                    </li>
                    <li className="lp-finding lp-finding--amber">
                      <span className="lp-finding-role">Compliance</span>
                      <span className="lp-finding-status">Conditional</span>
                    </li>
                  </ul>
                </div>

                <div className="lp-dp-next">
                  <p className="lp-dp-label">Next Action</p>
                  <p>Request missing security documents from vendor before proceeding.</p>
                </div>
              </div>
            </div>

            <div className="lp-section-cta">
              <a
                href="mailto:hilaytrivedi1224@gmail.com?subject=Tower%20of%20Agents%20Demo"
                className="lp-btn-primary"
              >
                Download Sample Packet
              </a>
            </div>
          </div>
        </section>

        {/* ── USE CASES ──────────────────────────────────────────────── */}
        <section className="lp-section lp-section--alt" id="use-cases" aria-labelledby="uc-heading">
          <div className="lp-container">
            <p className="eyebrow">Use Cases</p>
            <h2 id="uc-heading">One control tower. Multiple enterprise workflows.</h2>
            <div className="lp-cards lp-cards--4">
              {[
                { title: "Vendor Onboarding", desc: "Review vendor contracts, security posture, financial terms, and compliance requirements before onboarding.", status: "available" },
                { title: "HR Screening", desc: "Screen resumes, check policy alignment, flag inconsistencies, and produce structured candidate assessment packets.", status: "available" },
                { title: "Policy Exception Review", desc: "Route policy exception requests through relevant stakeholders with evidence-backed approval or denial.", status: "coming-soon" },
                { title: "Contract Review", desc: "Extract key clauses, flag risks, identify missing terms, and route contracts to the right reviewers automatically.", status: "coming-soon" },
                { title: "Engineering Change Review", desc: "Review code or architecture changes against security policies, compliance requirements, and engineering standards.", status: "coming-soon" },
                { title: "Customer Escalation", desc: "Triage and route customer escalations with context from CRM, past interactions, and SLA policies.", status: "" },
                { title: "Invoice Approval", desc: "Validate invoices against purchase orders, contracts, and budget allocations before routing for approval.", status: "" },
                { title: "Sales Lead Qualification", desc: "Score and qualify inbound leads against ICP criteria, company data, and past deal history.", status: "" },
              ].map(({ title, desc, status }) => (
                <div key={title} className="lp-card">
                  <div className="lp-uc-header">
                    <h3>{title}</h3>
                    {status === "available" && <span className="lp-badge lp-badge--green">Available now</span>}
                    {status === "coming-soon" && <span className="lp-badge lp-badge--muted">Coming soon</span>}
                  </div>
                  <p>{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── TRUST & GOVERNANCE ─────────────────────────────────────── */}
        <section className="lp-section" id="security" aria-labelledby="trust-heading">
          <div className="lp-container">
            <p className="eyebrow">Trust &amp; Governance</p>
            <h2 id="trust-heading">Built for control, not blind automation.</h2>
            <p className="lp-section-sub">
              Enterprise AI needs more than accuracy — it needs accountability, auditability, and
              the ability to say no.
            </p>
            <div className="lp-cards lp-cards--2 lp-cards--wide">
              {[
                { title: "Human approval", desc: "No workflow completes without a human sign-off. Every approval and override is logged with the reviewer, timestamp, and reason." },
                { title: "Evidence citations", desc: "Every agent finding links to the specific document section that supports it. Approvers can verify every claim before acting." },
                { title: "Role-based access control", desc: "Reviewers see only the workflows and decisions assigned to their role. Sensitive data is scoped at the organization level." },
                { title: "Sandbox mode", desc: "Run any workflow against real documents in a non-production sandbox before promoting to live. No decisions are logged or actionable." },
                { title: "Audit logs", desc: "Complete, tamper-evident logs of every agent run, document upload, finding, approval, and override. Exportable for compliance audits." },
                { title: "Model routing & control", desc: "Lock specific models to specific agents. Route sensitive workflows to private endpoints. Full visibility into what model made each decision." },
                { title: "BYOK / BYOM", desc: "Bring your own API keys and your own models. TOA never sees your API keys in shared infrastructure. Your keys, your endpoints, your data." },
                { title: "Self-hosted option", desc: "Deploy TOA entirely within your private cloud or on-premises infrastructure. No data leaves your environment. Available on the Enterprise plan." },
              ].map(({ title, desc }) => (
                <div key={title} className="lp-feature-row">
                  <div className="lp-feature-icon" aria-hidden="true">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                      <path d="M10 2l-7 3.5v5C3 14.9 6.1 18.5 10 20c3.9-1.5 7-5.1 7-9.5v-5L10 2z" stroke="var(--green)" strokeWidth="1.3" strokeLinejoin="round" />
                      <path d="M7 10l2 2 4-4" stroke="var(--green)" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>
                  <div>
                    <strong>{title}</strong>
                    <p>{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── VALUE PER TOKEN ────────────────────────────────────────── */}
        <section className="lp-section lp-section--alt" aria-labelledby="vpt-heading">
          <div className="lp-container">
            <p className="eyebrow">Efficiency</p>
            <h2 id="vpt-heading">Optimize value per token.</h2>
            <p className="lp-section-sub">
              TOA tracks the full cost and outcome of every workflow run so you can continuously
              improve the value you extract from every AI call. Route cheap tasks to efficient
              models; route high-stakes reasoning to the best available model. Pay for outcomes,
              not experimentation.
            </p>
            <div className="lp-metrics-grid" aria-label="Value metrics">
              {[
                { label: "Cost per workflow", desc: "Total model cost for a complete multi-agent run." },
                { label: "Cost per approved packet", desc: "What it actually costs to produce a decision humans approve." },
                { label: "Tokens per agent", desc: "Per-role token consumption broken down by task type." },
                { label: "Human approval rate", desc: "What percentage of packets are approved without override." },
                { label: "Override rate", desc: "How often humans override agent recommendations — your quality signal." },
                { label: "Risk detection score", desc: "How often agents surface risks that humans confirm as real." },
                { label: "Time saved per workflow", desc: "Measured against baseline manual review time." },
                { label: "Best model per agent", desc: "Which model delivers best accuracy/cost ratio for each role." },
              ].map(({ label, desc }) => (
                <div key={label} className="lp-metric-card">
                  <div className="lp-metric-label">{label}</div>
                  <div className="lp-metric-desc">{desc}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── DEPLOYMENT ─────────────────────────────────────────────── */}
        <section className="lp-section" aria-labelledby="deploy-heading">
          <div className="lp-container">
            <p className="eyebrow">Deployment</p>
            <h2 id="deploy-heading">Start hosted. Scale to private deployment.</h2>
            <div className="lp-deploy-grid">
              <div className="lp-deploy-col">
                <h3>Hosted SaaS</h3>
                <p>Get started in minutes. No infrastructure to manage.</p>
                <ul className="lp-feature-list">
                  <li>Instant setup, no DevOps required</li>
                  <li>Managed updates and security patches</li>
                  <li>Usage-based model cost tracking</li>
                  <li>Multi-tenant data isolation</li>
                  <li>SOC 2 roadmap for shared infra</li>
                </ul>
              </div>
              <div className="lp-deploy-col lp-deploy-col--featured">
                <h3>Private / Self-hosted</h3>
                <p>Full data sovereignty for regulated industries.</p>
                <ul className="lp-feature-list">
                  <li>Deploy in your private cloud or on-prem</li>
                  <li>No data leaves your infrastructure</li>
                  <li>Bring your own models and endpoints</li>
                  <li>Custom SSO / RBAC integration</li>
                  <li>Dedicated onboarding and SLA</li>
                </ul>
                <p className="lp-deploy-note">Available to design partners and Enterprise customers.</p>
              </div>
            </div>
          </div>
        </section>

        {/* ── WHO IT IS FOR ──────────────────────────────────────────── */}
        <section className="lp-section lp-section--alt" aria-labelledby="for-heading">
          <div className="lp-container">
            <p className="eyebrow">Who It&apos;s For</p>
            <h2 id="for-heading">Built for teams making repetitive but risky internal decisions.</h2>
            <div className="lp-audience-list" role="list">
              {[
                { role: "Operations", desc: "Standardize and speed up repetitive review cycles without adding headcount." },
                { role: "Procurement", desc: "Review vendors faster, enforce procurement policies consistently, and keep a complete audit trail." },
                { role: "HR", desc: "Screen candidates against job requirements and compliance criteria with structured, evidence-backed assessment packets." },
                { role: "Compliance", desc: "Ensure every decision references the right policy version and produces an exportable audit record." },
                { role: "Finance", desc: "Validate invoices, purchase orders, and budget requests against policy before they reach an approver." },
                { role: "Engineering", desc: "Review architecture and code changes against security policies and engineering standards at scale." },
                { role: "Founders / COOs", desc: "Build a single control layer for all AI-assisted decisions in your company — without building it from scratch." },
              ].map(({ role, desc }) => (
                <div key={role} className="lp-audience-row" role="listitem">
                  <div className="lp-audience-role">{role}</div>
                  <div className="lp-audience-desc">{desc}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── WHY NOW ────────────────────────────────────────────────── */}
        <section className="lp-section" aria-labelledby="whynow-heading">
          <div className="lp-container lp-why-inner">
            <div>
              <p className="eyebrow">Why Now</p>
              <h2 id="whynow-heading">Enterprise AI needs a control layer.</h2>
              <p>
                LLMs are capable enough to do real enterprise work — but they lack the structure,
                accountability, and auditability that enterprises require. Companies are deploying
                chatbots, copilots, and point automations — but they have no way to see what their
                AI is deciding, why, or whether it is right.
              </p>
              <p>
                Tower of Agents is the control layer. Not another AI model. Not another chatbot.
                The orchestration, evidence, and approval infrastructure that makes enterprise AI
                deployable, auditable, and improvable.
              </p>
            </div>
            <div className="lp-compare-table" role="table" aria-label="Chatbot vs Tower of Agents comparison">
              <div className="lp-compare-header" role="row">
                <div role="columnheader">Generic Chatbot</div>
                <div role="columnheader">Tower of Agents</div>
              </div>
              {[
                ["Unstructured text answer", "Structured decision packet"],
                ["No citations", "Every claim cites a source"],
                ["No roles or specialization", "Role-based specialist agents"],
                ["No human gate", "Human approval required"],
                ["No audit trail", "Complete, exportable audit log"],
                ["Black-box reasoning", "Agent findings visible per role"],
                ["Generic training data", "Your company's policies and rules"],
                ["No improvement loop", "Override → eval flywheel → better agents"],
              ].map(([left, right]) => (
                <div key={left} className="lp-compare-row" role="row">
                  <div className="lp-compare-neg" role="cell">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                      <path d="M11 3L3 11M3 3l8 8" stroke="var(--red)" strokeWidth="1.5" strokeLinecap="round" />
                    </svg>
                    {left}
                  </div>
                  <div className="lp-compare-pos" role="cell">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                      <path d="M2 7l3.5 3.5L12 4" stroke="var(--green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    {right}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── DEMO ───────────────────────────────────────────────────── */}
        <section className="lp-section lp-section--alt" id="demo" aria-labelledby="demo-heading">
          <div className="lp-container">
            <p className="eyebrow">Live Demo</p>
            <h2 id="demo-heading">See TOA review a vendor in minutes.</h2>
            <p className="lp-section-sub">
              In a 30-minute live demo, we run a real vendor onboarding review end-to-end, using
              your documents or sample data.
            </p>
            <ol className="lp-demo-steps" role="list">
              {[
                "Upload vendor documents (contract, SOC 2, financial summary)",
                "Six specialist agents run in parallel",
                "Risks are flagged with source citations",
                "A decision packet is generated in real time",
                "You review the packet and approve or override",
                "The full audit trail is shown",
              ].map((step, i) => (
                <li key={i} className="lp-demo-step">
                  <span className="lp-demo-num">{i + 1}</span>
                  {step}
                </li>
              ))}
            </ol>
            <div className="lp-section-cta">
              <a
                href="mailto:hilaytrivedi1224@gmail.com?subject=Tower%20of%20Agents%20Demo"
                className="lp-btn-primary lp-btn-large"
              >
                Book a Live Demo
              </a>
            </div>
          </div>
        </section>

        {/* ── PRICING ────────────────────────────────────────────────── */}
        <section className="lp-section" id="pricing" aria-labelledby="pricing-heading">
          <div className="lp-container">
            <p className="eyebrow">Pricing</p>
            <h2 id="pricing-heading">Simple pricing for pilots and teams.</h2>
            <div className="lp-pricing-grid">
              <div className="lp-pricing-card">
                <div className="lp-pricing-tier">Pilot</div>
                <div className="lp-pricing-price">$500–$2,000<span>/month</span></div>
                <p className="lp-pricing-desc">For design partners who want to prove value fast.</p>
                <ul className="lp-feature-list">
                  <li>Custom setup and onboarding</li>
                  <li>1 workflow</li>
                  <li>Decision packet output</li>
                  <li>Weekly feedback sessions</li>
                  <li>Direct founder access</li>
                </ul>
                <a href="#design-partner" className="lp-btn-ghost lp-btn-full">Apply as Design Partner</a>
              </div>

              <div className="lp-pricing-card lp-pricing-card--featured">
                <div className="lp-pricing-featured-badge">Recommended</div>
                <div className="lp-pricing-tier">Team</div>
                <div className="lp-pricing-price">$499<span>/month</span></div>
                <p className="lp-pricing-desc">For teams running multiple review workflows.</p>
                <ul className="lp-feature-list">
                  <li>3 workflows</li>
                  <li>Team workspace</li>
                  <li>Document upload and storage</li>
                  <li>Audit history</li>
                  <li>Model cost tracking</li>
                </ul>
                <a
                  href="mailto:hilaytrivedi1224@gmail.com?subject=Tower%20of%20Agents%20Demo"
                  className="lp-btn-primary lp-btn-full"
                >
                  Book a Demo
                </a>
              </div>

              <div className="lp-pricing-card">
                <div className="lp-pricing-tier">Enterprise</div>
                <div className="lp-pricing-price">Contact us</div>
                <p className="lp-pricing-desc">For regulated industries and large teams.</p>
                <ul className="lp-feature-list">
                  <li>Self-hosted or private cloud</li>
                  <li>BYOM / BYOK</li>
                  <li>SSO / RBAC</li>
                  <li>Advanced audit logs</li>
                  <li>Custom workflows</li>
                </ul>
                <a
                  href="mailto:hilaytrivedi1224@gmail.com?subject=Tower%20of%20Agents%20Enterprise"
                  className="lp-btn-ghost lp-btn-full"
                >
                  Contact us
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* ── DESIGN PARTNER ─────────────────────────────────────────── */}
        <section className="lp-section lp-section--alt" id="design-partner" aria-labelledby="dp-prog-heading">
          <div className="lp-container lp-dp-prog-inner">
            <div>
              <p className="eyebrow">Design Partner Program</p>
              <h2 id="dp-prog-heading">Become a design partner.</h2>
              <p className="lp-section-sub">
                We are working with a small cohort of early enterprise customers to build the
                workflows that matter most to them. Design partners shape the product roadmap and
                get priority access to every new module.
              </p>

              <h3 className="lp-sub-heading">Design partners get</h3>
              <ul className="lp-checklist">
                {[
                  "A custom workflow configured for your use case",
                  "Direct access to the founder and engineering team",
                  "Weekly review sessions and dedicated Slack channel",
                  "Pilot pricing with path to discounted annual contract",
                  "Roadmap input: your use case shapes what we build next",
                  "Early access to every new module",
                ].map((item) => (
                  <li key={item}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                      <path d="M3 8l3 3 7-7" stroke="var(--green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>

              <h3 className="lp-sub-heading" style={{ marginTop: "2rem" }}>Good fit if you</h3>
              <ul className="lp-checklist">
                {[
                  "Run document-heavy internal workflows today (vendor review, HR screening, contract review, policy exceptions)",
                  "Have 3–20 people involved in review cycles",
                  "Need an audit trail for compliance or legal reasons",
                  "Want AI assistance but cannot accept hallucinated, uncited answers",
                  "Are willing to give weekly feedback and share real documents for testing",
                ].map((item) => (
                  <li key={item}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                      <path d="M3 8l3 3 7-7" stroke="var(--green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <div className="lp-dp-cta-box">
              <h3>Apply as a Design Partner</h3>
              <p>Tell us about your workflow and we will follow up within 24 hours.</p>
              <a
                href="mailto:hilaytrivedi1224@gmail.com?subject=Tower%20of%20Agents%20Design%20Partner%20Application"
                className="lp-btn-primary lp-btn-full"
              >
                Apply as Design Partner
              </a>
              <p className="lp-dp-note">No commitment. We will confirm fit before any contract.</p>
            </div>
          </div>
        </section>

        {/* ── FOUNDER ────────────────────────────────────────────────── */}
        <section className="lp-section" aria-labelledby="founder-heading">
          <div className="lp-container">
            <p className="eyebrow">The Founder</p>
            <h2 id="founder-heading">Built by a founder obsessed with agentic enterprise systems.</h2>
            <div className="lp-founder-card">
              <div className="lp-founder-avatar" aria-hidden="true">
                <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
                  <circle cx="28" cy="28" r="28" fill="var(--line)" />
                  <circle cx="28" cy="22" r="10" fill="var(--muted)" />
                  <path d="M8 52c0-11 9-20 20-20s20 9 20 20" fill="var(--muted)" />
                </svg>
              </div>
              <div className="lp-founder-body">
                <div className="lp-founder-name">Hilay Trivedi</div>
                <p>
                  I have spent years watching enterprise teams drown in document review cycles —
                  inconsistent decisions, slow approvals, and no audit trail. I built Tower of
                  Agents because I believe enterprise AI needs a control layer, not just more
                  chatbots. TOA is the product I wish existed: role-based agents, evidence-backed
                  decisions, and a human always in the loop.
                </p>
                <div className="lp-founder-links">
                  <a
                    href="#"
                    aria-label="Hilay Trivedi on GitHub (link placeholder)"
                    className="lp-founder-link"
                  >
                    GitHub
                  </a>
                  <a
                    href="mailto:hilaytrivedi1224@gmail.com?subject=Tower%20of%20Agents%20Demo"
                    aria-label="Book a demo with Hilay"
                    className="lp-founder-link"
                  >
                    Book a Demo
                  </a>
                  <a
                    href="#"
                    aria-label="Hilay Trivedi on LinkedIn (link placeholder)"
                    className="lp-founder-link"
                  >
                    LinkedIn
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── FAQ ────────────────────────────────────────────────────── */}
        <section className="lp-section lp-section--alt" aria-labelledby="faq-heading">
          <div className="lp-container lp-faq-container">
            <p className="eyebrow">FAQ</p>
            <h2 id="faq-heading">Frequently asked questions.</h2>
            <FaqAccordion />
          </div>
        </section>

        {/* ── FINAL CTA ──────────────────────────────────────────────── */}
        <section className="lp-section lp-final-cta" aria-labelledby="finalcta-heading">
          <div className="lp-container lp-final-cta-inner">
            <p className="eyebrow">Get Started</p>
            <h2 id="finalcta-heading">Build your company&apos;s first AI workflow control tower.</h2>
            <p className="lp-section-sub">
              Start with one workflow. Most design partners are live within a week. No infrastructure
              required for the hosted plan.
            </p>
            <div className="lp-final-ctas">
              <a
                href="mailto:hilaytrivedi1224@gmail.com?subject=Tower%20of%20Agents%20Demo"
                className="lp-btn-primary lp-btn-large"
              >
                Book a Demo
              </a>
              <a href="#design-partner" className="lp-btn-ghost lp-btn-large">
                Apply as Design Partner
              </a>
            </div>
            <p className="lp-onboard-note">
              Most pilots go live within 1 week. Starts with a 30-minute scoping call.
            </p>
          </div>
        </section>
      </main>

      {/* ── FOOTER ─────────────────────────────────────────────────── */}
      <footer className="lp-footer" role="contentinfo">
        <div className="lp-container lp-footer-inner">
          <div className="lp-footer-brand">
            <Link href="/" className="lp-logo" aria-label="Tower of Agents home">
              <svg width="24" height="24" viewBox="0 0 28 28" fill="none" aria-hidden="true">
                <rect width="28" height="28" rx="6" fill="var(--green-dark)" />
                <rect x="8" y="8" width="5" height="5" rx="1" fill="var(--lime)" />
                <rect x="15" y="8" width="5" height="5" rx="1" fill="var(--lime)" opacity="0.6" />
                <rect x="8" y="15" width="5" height="5" rx="1" fill="var(--lime)" opacity="0.6" />
                <rect x="15" y="15" width="5" height="5" rx="1" fill="var(--lime)" />
              </svg>
              <span>Tower of Agents</span>
            </Link>
            <p className="lp-footer-tagline">AI control tower for enterprise workflows.</p>
            <div className="lp-footer-social">
              <a href="#" aria-label="Tower of Agents on GitHub (placeholder)">GitHub</a>
              <a href="#" aria-label="Tower of Agents on LinkedIn (placeholder)">LinkedIn</a>
              <a href="#" aria-label="Tower of Agents on X/Twitter (placeholder)">X / Twitter</a>
            </div>
          </div>

          <div className="lp-footer-links">
            <div className="lp-footer-col">
              <div className="lp-footer-col-title">Product</div>
              <ul role="list">
                <li><a href="#product">Overview</a></li>
                <li><a href="#how-it-works">How It Works</a></li>
                <li><a href="#decision-packet">Decision Packets</a></li>
                <li><a href="/dashboard">Open Product</a></li>
                <li><a href="/docs">Docs</a></li>
              </ul>
            </div>
            <div className="lp-footer-col">
              <div className="lp-footer-col-title">Use Cases</div>
              <ul role="list">
                <li><a href="#use-cases">Vendor Onboarding</a></li>
                <li><a href="#use-cases">HR Screening</a></li>
                <li><a href="#use-cases">Contract Review</a></li>
                <li><a href="#use-cases">Policy Review</a></li>
                <li><a href="#use-cases">Engineering Review</a></li>
              </ul>
            </div>
            <div className="lp-footer-col">
              <div className="lp-footer-col-title">Company</div>
              <ul role="list">
                <li><a href="#security">Security</a></li>
                <li><a href="#pricing">Pricing</a></li>
                <li><a href="#design-partner">Design Partner</a></li>
                <li><a href="mailto:hilaytrivedi1224@gmail.com">Contact</a></li>
              </ul>
            </div>
          </div>
        </div>
        <div className="lp-footer-bottom">
          <div className="lp-container">
            <p>
              &copy; {new Date().getFullYear()} Tower of Agents. Contact:{" "}
              <a href="mailto:hilaytrivedi1224@gmail.com">hilaytrivedi1224@gmail.com</a>
            </p>
          </div>
        </div>
      </footer>
    </>
  );
}
