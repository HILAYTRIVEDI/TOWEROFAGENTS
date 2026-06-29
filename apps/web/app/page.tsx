import Link from "next/link";

const roles = ["Procurement", "Compliance", "Finance", "HR", "Legal", "Security"];

const architectureSteps = [
  "Request",
  "Governance",
  "Execution",
  "Company Brain",
  "Specialist Agents",
  "Decision Engine",
  "Decision Packet",
  "Human Approval",
];

const pillars = [
  ["Governance", "Policy checks, approval gates, audit records, and scoped access before AI can act."],
  ["Execution", "Role-based agents run the review work and record findings by domain."],
  ["Company Brain", "Policies, thresholds, past decisions, and internal context ground every workflow."],
  ["Decision Intelligence", "Risk flags, disagreements, confidence signals, and recommended next actions."],
  ["Decision Packet", "A structured artifact a human can approve, override, store, and revisit."],
  ["Platform Operations", "Model routing, cost visibility, sandbox runs, and workflow observability."],
];

const packetFields = [
  ["Recommendation", "Conditional approval"],
  ["Executive summary", "Vendor can proceed after security evidence is supplied."],
  ["Evidence", "Contract v3, DPA, pricing sheet, security questionnaire"],
  ["Risk flags", "Missing SOC 2; unclear data retention; auto-renewal clause"],
  ["Agent findings", "Procurement approved; Legal needs review; Security blocked"],
  ["Next actions", "Request SOC 2 and route renewal clause to Legal"],
  ["Approval", "Human sign-off required before onboarding"],
];

const workflows = {
  available: ["Vendor onboarding", "Procurement review", "HR candidate screening"],
  soon: ["Finance exception review", "Legal contract review", "Engineering change review", "Security review", "Sales lead qualification"],
};

const comparisonRows = [
  ["Unstructured chat answer", "Structured decision packet"],
  ["Generic model memory", "Company policies and past decisions"],
  ["Single assistant voice", "Specialist agents by business role"],
  ["No approval gate", "Human approval before action"],
  ["Weak citations", "Evidence-backed findings"],
  ["No audit trail", "Complete workflow audit record"],
  ["Hard to evaluate", "Override and evaluation loop"],
  ["Point automation", "Cross-department control layer"],
];

const governanceSignals = [
  "Human approval",
  "Policy engine",
  "Role-scoped access",
  "Evidence citations",
  "Audit history",
  "Model routing",
  "Sandbox runs",
  "Evaluation loop",
];

const metrics = [
  ["Pilot target", "8 hrs to 45 min", "Review-cycle compression goal"],
  ["Quality signal", "Override rate", "Tracked per workflow"],
  ["Control signal", "100%", "Packets require human approval"],
];

const departments = ["Procurement", "HR", "Finance", "Legal", "Security", "Engineering"];

const faqs = [
  ["What is Tower of Agents?", "A governance and execution layer for enterprise AI workflows. It turns requests, documents, and company policy into evidence-backed decision packets."],
  ["How is it different from a chatbot?", "Chatbots produce answers. TOA runs a governed workflow with specialist agents, cited findings, approval status, and an audit trail."],
  ["What workflow should we start with?", "Vendor onboarding, procurement review, and HR candidate screening are the current best-fit MVP workflows."],
  ["Does AI make the final decision?", "No. Agent outputs are advisory, and high-impact decisions require human review and approval."],
  ["Can we bring our own models?", "The architecture is BYOM-ready, with model routing intended to support different providers and private endpoints."],
  ["Is this production-ready for every department?", "No. The MVP focuses on a few deep workflows first, then expands once the governance loop is proven."],
];

function Logo() {
  return (
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
  );
}

function ArchitectureFlow({ compact = false }: { compact?: boolean }) {
  const steps = compact
    ? ["Request", "Governance", "Execution", "Decision Packet", "Human Approval"]
    : architectureSteps;

  return (
    <ol className="toa-arch-flow" aria-label="Tower of Agents architecture flow">
      {steps.map((step, index) => (
        <li key={step} className="toa-arch-step">
          <span className="toa-arch-index">{String(index + 1).padStart(2, "0")}</span>
          <span>{step}</span>
        </li>
      ))}
    </ol>
  );
}

export default function HomePage() {
  return (
    <>
      <header className="lp-nav-wrap" role="banner">
        <nav className="lp-nav" aria-label="Main navigation">
          <Logo />
          <ul className="lp-nav-links" role="list">
            <li><a href="#product">Product</a></li>
            <li><a href="#architecture">Architecture</a></li>
            <li><a href="#governance">Governance</a></li>
            <li><a href="#workflows">Workflows</a></li>
            <li><a href="/docs">Docs</a></li>
          </ul>
          <a href="#partner" className="lp-btn-primary">Start Design Partner</a>
        </nav>
      </header>

      <main id="main-content" className="toa-landing">
        <section className="toa-hero" aria-labelledby="hero-heading">
          <div className="lp-container toa-hero-grid">
            <div>
              <p className="eyebrow">Enterprise AI Control Layer</p>
              <h1 id="hero-heading">The Governance &amp; Execution Layer for Enterprise AI</h1>
              <p className="toa-hero-sub">
                Deploy AI into mission-critical workflows with policy-aware execution,
                evidence-backed decisions, and human approval.
              </p>
              <div className="toa-ctas">
                <a href="#partner" className="lp-btn-primary">Start Design Partner</a>
                <a href="#decision-packet" className="lp-btn-ghost">View Decision Packet</a>
              </div>
            </div>
            <div className="toa-hero-visual" aria-label="Request to approval architecture">
              <ArchitectureFlow compact />
            </div>
          </div>
        </section>

        <section className="toa-designed-for" aria-label="Designed for">
          <div className="lp-container toa-badge-strip">
            {roles.map((role) => <span key={role}>{role}</span>)}
          </div>
        </section>

        <section className="toa-section" id="problem" aria-labelledby="problem-heading">
          <div className="lp-container">
            <p className="eyebrow">The Problem</p>
            <h2 id="problem-heading">Enterprise AI is powerful, but not yet accountable.</h2>
            <div className="toa-problem-cards">
              {[
                ["AI cannot be trusted", "Generic answers hallucinate, skip evidence, and collapse under audit."],
                ["Reviews are painfully slow", "Documents move across teams while decisions wait in email and chat."],
                ["Nobody governs AI", "Policy, access, approvals, and model behavior drift across tools."],
              ].map(([title, copy]) => (
                <article key={title} className="toa-card">
                  <h3>{title}</h3>
                  <p>{copy}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="toa-section toa-section-alt" id="product" aria-labelledby="solution-heading">
          <div className="lp-container">
            <p className="eyebrow">The Solution</p>
            <h2 id="solution-heading">Govern the work. Execute the review. Package the decision.</h2>
            <div className="toa-solution-split">
              <article>
                <span className="toa-panel-label">Governance</span>
                <h3>Control before automation</h3>
                <ul>
                  <li>Policy-aware workflows</li>
                  <li>Human approval gates</li>
                  <li>Role-scoped access</li>
                  <li>Auditable records</li>
                </ul>
              </article>
              <article>
                <span className="toa-panel-label">Execution</span>
                <h3>Specialists do the work</h3>
                <ul>
                  <li>Document review agents</li>
                  <li>Evidence-backed findings</li>
                  <li>Risk and disagreement surfacing</li>
                  <li>Decision packet synthesis</li>
                </ul>
              </article>
            </div>
          </div>
        </section>

        <section className="toa-section" id="architecture" aria-labelledby="architecture-heading">
          <div className="lp-container toa-two-col">
            <div>
              <p className="eyebrow">Architecture</p>
              <h2 id="architecture-heading">A governed path from request to approval.</h2>
              <p className="toa-muted">
                TOA is the layer between business teams and AI execution: it routes context,
                applies policy, coordinates agents, and produces the artifact a human can trust.
              </p>
            </div>
            <ArchitectureFlow />
          </div>
        </section>

        <section className="toa-section toa-section-alt" aria-labelledby="pillars-heading">
          <div className="lp-container">
            <p className="eyebrow">Product Pillars</p>
            <h2 id="pillars-heading">Six primitives for governed AI work.</h2>
            <div className="toa-pillar-grid">
              {pillars.map(([title, copy]) => (
                <article key={title} className="toa-card">
                  <h3>{title}</h3>
                  <p>{copy}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="toa-section" id="how-it-works" aria-labelledby="how-heading">
          <div className="lp-container">
            <p className="eyebrow">How It Works</p>
            <h2 id="how-heading">Six steps from intake to governed decision.</h2>
            <ol className="toa-steps" role="list">
              {["Submit request", "Attach documents", "Apply policy", "Run agents", "Generate packet", "Approve or override"].map((step, index) => (
                <li key={step}>
                  <span>{index + 1}</span>
                  {step}
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="toa-section toa-section-alt" id="decision-packet" aria-labelledby="packet-heading">
          <div className="lp-container">
            <p className="eyebrow">Decision Packet</p>
            <h2 id="packet-heading">The product is the packet.</h2>
            <div className="toa-packet-showcase">
              <div>
                <span className="toa-status">Human Approval Required</span>
                <h3>Acme Analytics Vendor Review</h3>
                <p>
                  A compact, auditable packet with the recommendation, cited evidence,
                  role-level findings, risk flags, and next action.
                </p>
              </div>
              <dl>
                {packetFields.map(([label, value]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>
        </section>

        <section className="toa-section" id="workflows" aria-labelledby="workflows-heading">
          <div className="lp-container">
            <p className="eyebrow">Available Workflows</p>
            <h2 id="workflows-heading">Start narrow. Expand once trust is proven.</h2>
            <div className="toa-available-grid">
              <article>
                <h3>Available Today</h3>
                {workflows.available.map((item) => <span key={item}>{item}</span>)}
              </article>
              <article>
                <h3>Coming Soon</h3>
                {workflows.soon.map((item) => <span key={item}>{item}</span>)}
              </article>
            </div>
          </div>
        </section>

        <section className="toa-section toa-section-alt" aria-labelledby="comparison-heading">
          <div className="lp-container">
            <p className="eyebrow">Comparison</p>
            <h2 id="comparison-heading">Generic AI answers questions. TOA governs decisions.</h2>
            <div className="toa-compare-table" role="table" aria-label="Generic AI compared with Tower of Agents">
              <div role="row">
                <strong role="columnheader">Generic AI</strong>
                <strong role="columnheader">Tower of Agents</strong>
              </div>
              {comparisonRows.map(([generic, toa]) => (
                <div key={generic} role="row">
                  <span role="cell">{generic}</span>
                  <span role="cell">{toa}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="toa-section" id="governance" aria-labelledby="governance-heading">
          <div className="lp-container">
            <p className="eyebrow">Enterprise Governance</p>
            <h2 id="governance-heading">Built for control, not blind automation.</h2>
            <div className="toa-governance-grid">
              {governanceSignals.map((signal) => <span key={signal}>{signal}</span>)}
            </div>
          </div>
        </section>

        <section className="toa-section toa-section-alt" aria-labelledby="metrics-heading">
          <div className="lp-container">
            <p className="eyebrow">Metrics</p>
            <h2 id="metrics-heading">Measure the control loop before claiming scale.</h2>
            <div className="toa-metrics-row">
              {metrics.map(([label, value, copy]) => (
                <article key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                  <p>{copy}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="toa-section" aria-labelledby="vision-heading">
          <div className="lp-container toa-two-col">
            <div>
              <p className="eyebrow">Platform Vision</p>
              <h2 id="vision-heading">One decision layer across every department.</h2>
              <p className="toa-muted">
                The MVP proves one deep workflow first. The platform vision is every risky,
                document-heavy decision flowing through the same governed operating layer.
              </p>
            </div>
            <div className="toa-vision-cascade">
              {departments.map((department) => <span key={department}>{department} through TOA</span>)}
            </div>
          </div>
        </section>

        <section className="toa-section toa-section-alt toa-partner-section" id="partner" aria-labelledby="partner-heading">
          <div className="lp-container toa-two-col">
            <div>
              <p className="eyebrow">Design Partner</p>
              <h2 id="partner-heading">Looking for 5 design partners.</h2>
              <p className="toa-muted">
                Best fit: teams with document-heavy workflows, audit pressure, and a human
                review step they cannot remove.
              </p>
            </div>
            <ul>
              <li>Configure one real workflow</li>
              <li>Review real packets weekly</li>
              <li>Shape governance and approval UX</li>
              <li>Get direct founder support</li>
            </ul>
          </div>
        </section>

        <section className="toa-section" aria-labelledby="founder-heading">
          <div className="lp-container toa-founder">
            <p className="eyebrow">Founder</p>
            <h2 id="founder-heading">Built by Hilay Trivedi.</h2>
            <p>
              Tower of Agents exists because enterprise AI needs a control layer: not another
              chat window, but governed execution, evidence-backed decisions, and humans in the loop.
            </p>
            <a href="mailto:hilaytrivedi1224@gmail.com">hilaytrivedi1224@gmail.com</a>
          </div>
        </section>

        <section className="toa-section toa-section-alt" aria-labelledby="faq-heading">
          <div className="lp-container">
            <p className="eyebrow">FAQ</p>
            <h2 id="faq-heading">Questions enterprise teams ask first.</h2>
            <div className="toa-faq">
              {faqs.map(([question, answer]) => (
                <details key={question}>
                  <summary>{question}</summary>
                  <p>{answer}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="toa-final-cta" aria-labelledby="final-heading">
          <div className="lp-container">
            <p className="eyebrow">Ready?</p>
            <h2 id="final-heading">Ready to deploy AI safely?</h2>
            <a href="#partner" className="lp-btn-primary lp-btn-large">Start Design Partner</a>
          </div>
        </section>
      </main>

      <footer className="lp-footer" role="contentinfo">
        <div className="lp-container lp-footer-inner">
          <Logo />
          <p className="lp-footer-tagline">Governed execution for enterprise AI workflows.</p>
          <a href="mailto:hilaytrivedi1224@gmail.com">Contact</a>
        </div>
      </footer>
    </>
  );
}
