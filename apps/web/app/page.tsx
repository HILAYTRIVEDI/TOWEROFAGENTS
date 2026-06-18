import Link from "next/link";

export default function LandingPage() {
  return (
    <>
      {/* ── Top bar ── */}
      <header className="lp-topbar" role="banner">
        <Link href="/" className="lp-topbar-brand" aria-label="ATower home">
          <span className="lp-brand-mark" aria-hidden="true">A</span>
          <span className="lp-brand-wordmark">ATower</span>
        </Link>
        <nav aria-label="Site navigation">
          <Link href="/dashboard" className="button primary lp-topbar-cta">
            Open dashboard
          </Link>
        </nav>
      </header>

      <main>
        {/* ── Hero ── */}
        <section className="lp-hero" aria-labelledby="hero-heading">
          <div className="lp-hero-inner">
            <p className="eyebrow lp-eyebrow">Enterprise AI-agent control tower</p>
            <h1 id="hero-heading">
              Orchestrate specialist agents.<br />
              Keep humans in control.
            </h1>
            <p className="lede">
              ATower is an enterprise workflow control tower that routes complex decisions
              through specialist AI agents — with Band-backed collaboration, full audit
              trails, and mandatory human review at every high-impact step.
            </p>
            <div className="lp-hero-actions">
              <Link href="/dashboard" className="button primary lp-btn-lg">
                Open dashboard
              </Link>
              <Link href="/docs" className="button lp-btn-lg lp-btn-ghost">
                Read the docs
              </Link>
            </div>
          </div>
        </section>

        {/* ── Architecture story ── */}
        <section className="lp-section lp-arch-section" aria-labelledby="arch-heading">
          <div className="lp-section-inner">
            <p className="eyebrow lp-eyebrow">Real architecture</p>
            <h2 id="arch-heading" className="lp-section-title">
              One coherent pipeline — no black boxes
            </h2>
            <p className="lp-section-lede">
              Every layer is a first-class engineering concern. The control plane is fully
              inspectable from dashboard to database.
            </p>

            <div className="lp-arch-pipeline" role="img" aria-label="Architecture pipeline: Next.js dashboard to FastAPI to Supabase, LangGraph, and Band, then to AIML API and Featherless behind a single LLM interface">
              <div className="lp-arch-node lp-arch-node--primary">
                <span className="lp-arch-label">Frontend</span>
                <strong>Next.js Dashboard</strong>
                <span className="lp-arch-sub">App Router · React Server Components</span>
              </div>
              <div className="lp-arch-arrow" aria-hidden="true">→</div>
              <div className="lp-arch-node lp-arch-node--primary">
                <span className="lp-arch-label">API layer</span>
                <strong>FastAPI</strong>
                <span className="lp-arch-sub">Python · typed routes · async</span>
              </div>
              <div className="lp-arch-arrow" aria-hidden="true">→</div>
              <div className="lp-arch-cluster">
                <div className="lp-arch-node lp-arch-node--secondary">
                  <strong>Supabase</strong>
                  <span className="lp-arch-sub">Auth · Postgres · Storage · pgvector</span>
                </div>
                <div className="lp-arch-node lp-arch-node--secondary">
                  <strong>LangGraph</strong>
                  <span className="lp-arch-sub">Workflow runtime · agent graphs</span>
                </div>
                <div className="lp-arch-node lp-arch-node--band">
                  <strong>Band</strong>
                  <span className="lp-arch-sub">Collaboration · audit rooms</span>
                </div>
              </div>
              <div className="lp-arch-arrow" aria-hidden="true">→</div>
              <div className="lp-arch-node lp-arch-node--llm">
                <span className="lp-arch-label">LLM interface</span>
                <strong>One provider API</strong>
                <span className="lp-arch-sub">AIML API (routing / synthesis)</span>
                <span className="lp-arch-sub">Featherless (verification / second opinions)</span>
              </div>
            </div>

            <div className="lp-callout" role="note">
              <div className="lp-callout-icon" aria-hidden="true">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.5"/>
                  <path d="M10 6v4m0 3v.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
              </div>
              <div>
                <strong>Band is the collaboration and audit layer.</strong>
                {" "}Agent findings are persisted to Supabase and posted to Band rooms in real time —
                every decision has a traceable, human-readable record before it reaches a reviewer.
              </div>
            </div>
          </div>
        </section>

        {/* ── HR Candidate Screening spotlight ── */}
        <section className="lp-section lp-spotlight-section" aria-labelledby="spotlight-heading">
          <div className="lp-section-inner">
            <p className="eyebrow lp-eyebrow">Proof workflow</p>
            <h2 id="spotlight-heading" className="lp-section-title">
              HR Candidate Screening
            </h2>
            <p className="lp-section-lede">
              The deepest workflow in the MVP — demonstrating the full agent lifecycle from
              intake through specialist analysis to human decision.
            </p>

            <div className="lp-pipeline-steps" role="list">
              <div className="lp-step" role="listitem">
                <div className="lp-step-num" aria-hidden="true">01</div>
                <h3 className="lp-step-title">Intake</h3>
                <p className="lp-step-body">
                  Job description and candidate resume submitted via structured form.
                  Artifacts stored in Supabase Storage; metadata indexed in Postgres.
                </p>
              </div>
              <div className="lp-step-connector" aria-hidden="true" />
              <div className="lp-step" role="listitem">
                <div className="lp-step-num" aria-hidden="true">02</div>
                <h3 className="lp-step-title">Specialist agents</h3>
                <p className="lp-step-body">
                  LangGraph routes the run through parallel specialist agents: skills
                  alignment, culture fit, experience depth, and red-flag detection.
                  Each agent posts findings to its Band room.
                </p>
              </div>
              <div className="lp-step-connector" aria-hidden="true" />
              <div className="lp-step" role="listitem">
                <div className="lp-step-num" aria-hidden="true">03</div>
                <h3 className="lp-step-title">Human review</h3>
                <p className="lp-step-body">
                  A consolidated advisory report surfaces in the dashboard.
                  Agent outputs are recommendations only — the hiring decision
                  always belongs to a human reviewer.
                </p>
              </div>
            </div>

            <p className="lp-advisory-note">
              <strong>Advisory outputs only.</strong>{" "}
              Agent recommendations inform, not replace, human judgment. High-impact decisions
              require explicit human approval before any action is taken.
            </p>
          </div>
        </section>

        {/* ── Capability cards ── */}
        <section className="lp-section" aria-labelledby="caps-heading">
          <div className="lp-section-inner">
            <p className="eyebrow lp-eyebrow">Platform capabilities</p>
            <h2 id="caps-heading" className="lp-section-title">
              Built for enterprise-grade workflows
            </h2>
            <div className="lp-cap-grid">
              <article className="lp-cap-card" aria-label="Multi-agent workflows">
                <div className="lp-cap-icon" aria-hidden="true">
                  <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                    <circle cx="5" cy="11" r="3" stroke="currentColor" strokeWidth="1.5"/>
                    <circle cx="17" cy="5" r="3" stroke="currentColor" strokeWidth="1.5"/>
                    <circle cx="17" cy="17" r="3" stroke="currentColor" strokeWidth="1.5"/>
                    <path d="M8 11h3m3-3.5-3 3m0 0 3 3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                </div>
                <h3 className="lp-cap-title">Multi-agent workflows</h3>
                <p className="lp-cap-body">
                  LangGraph-powered agent graphs with parallel specialist lanes,
                  typed handoffs, and retry logic baked in.
                </p>
              </article>

              <article className="lp-cap-card" aria-label="RAG knowledge base">
                <div className="lp-cap-icon" aria-hidden="true">
                  <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                    <rect x="3" y="3" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/>
                    <rect x="12" y="3" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/>
                    <rect x="3" y="12" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/>
                    <rect x="12" y="12" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/>
                  </svg>
                </div>
                <h3 className="lp-cap-title">RAG knowledge base</h3>
                <p className="lp-cap-body">
                  Documents indexed via pgvector in Supabase. Agents retrieve relevant
                  context at runtime — no hallucinated citations.
                </p>
              </article>

              <article className="lp-cap-card" aria-label="Band collaboration and audit">
                <div className="lp-cap-icon" aria-hidden="true">
                  <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                    <path d="M4 6h14M4 11h10M4 16h7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                </div>
                <h3 className="lp-cap-title">Band collaboration &amp; audit</h3>
                <p className="lp-cap-body">
                  Every agent finding is posted to a Band room. The full decision
                  thread is auditable, shareable, and persisted alongside the run record.
                </p>
              </article>

              <article className="lp-cap-card" aria-label="Human-in-the-loop review">
                <div className="lp-cap-icon" aria-hidden="true">
                  <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                    <circle cx="11" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.5"/>
                    <path d="M4 19c0-3.866 3.134-7 7-7h0c3.866 0 7 3.134 7 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                    <path d="M15 13l1.5 1.5L19 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <h3 className="lp-cap-title">Human-in-the-loop</h3>
                <p className="lp-cap-body">
                  Agent outputs are advisory. High-impact decisions gate on explicit
                  human approval — the system cannot act autonomously on consequential choices.
                </p>
              </article>
            </div>
          </div>
        </section>

        {/* ── Workflow templates ── */}
        <section className="lp-section" aria-labelledby="templates-heading">
          <div className="lp-section-inner">
            <p className="eyebrow lp-eyebrow">Workflow templates</p>
            <h2 id="templates-heading" className="lp-section-title">
              Start from a proven template
            </h2>
            <div className="lp-template-row">
              <article className="lp-tpl-card lp-tpl-card--featured" aria-label="HR Candidate Screening — deep workflow">
                <span className="tag">Deep workflow</span>
                <span className="lp-tpl-index" aria-hidden="true">01</span>
                <h3 className="lp-tpl-title">HR Candidate Screening</h3>
                <p className="lp-tpl-body">
                  Intake to specialist agents to human hire/no-hire review.
                  The full proof-of-concept workflow with parallel lanes and Band audit.
                </p>
                <Link href="/workflows/new" className="button primary lp-tpl-cta">
                  Start workflow
                </Link>
              </article>

              <article className="lp-tpl-card" aria-label="Sales Lead Qualification — template">
                <span className="tag">Template</span>
                <span className="lp-tpl-index" aria-hidden="true">02</span>
                <h3 className="lp-tpl-title">Sales Lead Qualification</h3>
                <p className="lp-tpl-body">
                  Score and route inbound leads through ICP-fit, intent, and
                  budget agents before handing off to an account executive.
                </p>
                <Link href="/workflows/new" className="button lp-tpl-cta">
                  Use template
                </Link>
              </article>

              <article className="lp-tpl-card" aria-label="Engineering Change Review — template">
                <span className="tag">Template</span>
                <span className="lp-tpl-index" aria-hidden="true">03</span>
                <h3 className="lp-tpl-title">Engineering Change Review</h3>
                <p className="lp-tpl-body">
                  Route change requests through impact analysis, dependency check,
                  and risk scoring agents before an engineer approves.
                </p>
                <Link href="/workflows/new" className="button lp-tpl-cta">
                  Use template
                </Link>
              </article>
            </div>
          </div>
        </section>

        {/* ── CTA band ── */}
        <section className="lp-cta-band" aria-labelledby="cta-heading">
          <div className="lp-cta-inner">
            <h2 id="cta-heading" className="lp-cta-title">
              Ready to run your first workflow?
            </h2>
            <p className="lp-cta-body">
              Open the dashboard and start a run from any template in under two minutes.
            </p>
            <div className="lp-hero-actions">
              <Link href="/dashboard" className="button lp-btn-lg lp-btn-lime">
                Open dashboard
              </Link>
              <Link href="/docs" className="button lp-btn-lg lp-btn-ghost-dark">
                Read the docs
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="lp-footer" role="contentinfo">
        <div className="lp-footer-inner">
          <div className="lp-footer-brand">
            <span className="lp-brand-mark lp-brand-mark--sm" aria-hidden="true">A</span>
            <span className="lp-brand-wordmark">ATower Of Agents</span>
          </div>
          <nav aria-label="Footer navigation" className="lp-footer-nav">
            <Link href="/dashboard">Dashboard</Link>
            <Link href="/workflows">Workflows</Link>
            <Link href="/agents">Agents</Link>
            <Link href="/knowledge-base">Knowledge base</Link>
            <Link href="/docs">Docs</Link>
          </nav>
          <p className="lp-footer-note">
            Agent outputs are advisory. High-impact decisions require human review.
          </p>
        </div>
      </footer>
    </>
  );
}
