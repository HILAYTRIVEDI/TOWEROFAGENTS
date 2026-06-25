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
            <p className="eyebrow lp-eyebrow">Decision-ready work, faster</p>
            <h1 id="hero-heading">
              Turn messy reviews into clear, auditable decisions.
            </h1>
            <p className="lede">
              ATower helps teams screen candidates, qualify opportunities, and review
              changes with evidence in one place, clear recommendations, and human
              approval before any high-impact action.
            </p>
            <div className="lp-hero-actions">
              <Link href="/dashboard" className="button primary lp-btn-lg">
                Review work queue
              </Link>
              <Link href="/workflows/new" className="button lp-btn-lg lp-btn-ghost">
                Start a workflow
              </Link>
            </div>
          </div>
        </section>

        {/* ── Outcome story ── */}
        <section className="lp-section lp-arch-section" aria-labelledby="arch-heading">
          <div className="lp-section-inner">
            <p className="eyebrow lp-eyebrow">What teams get</p>
            <h2 id="arch-heading" className="lp-section-title">
              From scattered inputs to a decision packet
            </h2>
            <p className="lp-section-lede">
              Operators do not need to chase files, chat threads, or model outputs.
              ATower gathers the evidence, runs the review, and leaves a clean record
              for the person accountable for the decision.
            </p>

            <div className="lp-arch-pipeline" role="img" aria-label="Outcome flow: upload source materials, compare evidence, surface review notes, and produce a human-reviewed decision packet">
              <div className="lp-arch-node lp-arch-node--primary">
                <span className="lp-arch-label">Intake</span>
                <strong>Bring the evidence together</strong>
                <span className="lp-arch-sub">Resumes, job descriptions, policies, notes, and supporting files</span>
              </div>
              <div className="lp-arch-arrow" aria-hidden="true">→</div>
              <div className="lp-arch-node lp-arch-node--primary">
                <span className="lp-arch-label">Review</span>
                <strong>Find strengths, gaps, and risks</strong>
                <span className="lp-arch-sub">Specialist reviews turn raw material into concise findings</span>
              </div>
              <div className="lp-arch-arrow" aria-hidden="true">→</div>
              <div className="lp-arch-cluster">
                <div className="lp-arch-node lp-arch-node--secondary">
                  <strong>Evidence-backed notes</strong>
                  <span className="lp-arch-sub">Recommendations point back to retrieved context</span>
                </div>
                <div className="lp-arch-node lp-arch-node--secondary">
                  <strong>Shared discussion</strong>
                  <span className="lp-arch-sub">Teams can follow the review trail in one room</span>
                </div>
                <div className="lp-arch-node lp-arch-node--band">
                  <strong>Human checkpoint</strong>
                  <span className="lp-arch-sub">AI output stays advisory until a reviewer acts</span>
                </div>
              </div>
              <div className="lp-arch-arrow" aria-hidden="true">→</div>
              <div className="lp-arch-node lp-arch-node--llm">
                <span className="lp-arch-label">Outcome</span>
                <strong>Decision packet</strong>
                <span className="lp-arch-sub">Recommendation, rationale, gaps, interview prompts, and audit trail</span>
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
                <strong>The result is not another chat transcript.</strong>
                {" "}Each run produces a structured packet reviewers can inspect, challenge,
                and approve with the supporting evidence still attached.
              </div>
            </div>
          </div>
        </section>

        {/* ── HR Candidate Screening spotlight ── */}
        <section className="lp-section lp-spotlight-section" aria-labelledby="spotlight-heading">
          <div className="lp-section-inner">
            <p className="eyebrow lp-eyebrow">First proven workflow</p>
            <h2 id="spotlight-heading" className="lp-section-title">
              HR Candidate Screening
            </h2>
            <p className="lp-section-lede">
              Help hiring teams move from scattered resumes and policies to a fairer,
              faster review packet that still leaves the final call with a person.
            </p>

            <div className="lp-pipeline-steps" role="list">
              <div className="lp-step" role="listitem">
                <div className="lp-step-num" aria-hidden="true">01</div>
                <h3 className="lp-step-title">Collect the case</h3>
                <p className="lp-step-body">
                  Upload the resume, job description, and hiring policy so the review
                  starts from the same source material every time.
                </p>
              </div>
              <div className="lp-step-connector" aria-hidden="true" />
              <div className="lp-step" role="listitem">
                <div className="lp-step-num" aria-hidden="true">02</div>
                <h3 className="lp-step-title">Compare what matters</h3>
                <p className="lp-step-body">
                  Surface role fit, missing evidence, policy concerns, bias checks,
                  and interview questions without losing the source context.
                </p>
              </div>
              <div className="lp-step-connector" aria-hidden="true" />
              <div className="lp-step" role="listitem">
                <div className="lp-step-num" aria-hidden="true">03</div>
                <h3 className="lp-step-title">Decide with a record</h3>
                <p className="lp-step-body">
                  Review a consolidated recommendation, challenge the reasoning,
                  and keep a traceable record before taking action.
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

        {/* ── Outcome cards ── */}
        <section className="lp-section" aria-labelledby="caps-heading">
          <div className="lp-section-inner">
            <p className="eyebrow lp-eyebrow">Product outcomes</p>
            <h2 id="caps-heading" className="lp-section-title">
              Review work without losing accountability
            </h2>
            <div className="lp-cap-grid">
              <article className="lp-cap-card" aria-label="Faster review cycles">
                <div className="lp-cap-icon" aria-hidden="true">
                  <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                    <circle cx="5" cy="11" r="3" stroke="currentColor" strokeWidth="1.5"/>
                    <circle cx="17" cy="5" r="3" stroke="currentColor" strokeWidth="1.5"/>
                    <circle cx="17" cy="17" r="3" stroke="currentColor" strokeWidth="1.5"/>
                    <path d="M8 11h3m3-3.5-3 3m0 0 3 3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                </div>
                <h3 className="lp-cap-title">Faster review cycles</h3>
                <p className="lp-cap-body">
                  Turn long-form artifacts into focused findings so reviewers spend
                  less time assembling context and more time making judgment calls.
                </p>
              </article>

              <article className="lp-cap-card" aria-label="Evidence-backed recommendations">
                <div className="lp-cap-icon" aria-hidden="true">
                  <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                    <rect x="3" y="3" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/>
                    <rect x="12" y="3" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/>
                    <rect x="3" y="12" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/>
                    <rect x="12" y="12" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/>
                  </svg>
                </div>
                <h3 className="lp-cap-title">Evidence-backed recommendations</h3>
                <p className="lp-cap-body">
                  Keep source documents attached to the review so teams can verify
                  why a strength, gap, or risk was raised.
                </p>
              </article>

              <article className="lp-cap-card" aria-label="Audit-ready collaboration">
                <div className="lp-cap-icon" aria-hidden="true">
                  <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                    <path d="M4 6h14M4 11h10M4 16h7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                </div>
                <h3 className="lp-cap-title">Audit-ready collaboration</h3>
                <p className="lp-cap-body">
                  Keep the discussion, findings, and final packet connected so
                  stakeholders can retrace what happened later.
                </p>
              </article>

              <article className="lp-cap-card" aria-label="Human-owned decisions">
                <div className="lp-cap-icon" aria-hidden="true">
                  <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                    <circle cx="11" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.5"/>
                    <path d="M4 19c0-3.866 3.134-7 7-7h0c3.866 0 7 3.134 7 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                    <path d="M15 13l1.5 1.5L19 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <h3 className="lp-cap-title">Human-owned decisions</h3>
                <p className="lp-cap-body">
                  Recommendations stay advisory. High-impact outcomes require a
                  reviewer to inspect the packet and make the call.
                </p>
              </article>
            </div>
          </div>
        </section>

        {/* ── Workflow templates ── */}
        <section className="lp-section" aria-labelledby="templates-heading">
          <div className="lp-section-inner">
            <p className="eyebrow lp-eyebrow">Where it helps</p>
            <h2 id="templates-heading" className="lp-section-title">
              Start with repeatable decision work
            </h2>
            <div className="lp-template-row">
              <article className="lp-tpl-card lp-tpl-card--featured" aria-label="HR Candidate Screening — deep workflow">
                <span className="tag">Deep workflow</span>
                <span className="lp-tpl-index" aria-hidden="true">01</span>
                <h3 className="lp-tpl-title">HR Candidate Screening</h3>
                <p className="lp-tpl-body">
                  Compare candidates against the role and policy, then hand reviewers
                  a concise packet with strengths, gaps, questions, and risk notes.
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
                  Triage inbound leads by fit, urgency, and missing context before
                  an account executive spends time on the account.
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
                  Summarize change impact, dependencies, and review risks so
                  engineers can approve with better context.
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
              Ready to review a real decision?
            </h2>
            <p className="lp-cta-body">
              Start with HR Candidate Screening and produce a decision packet your
              team can actually inspect.
            </p>
            <div className="lp-hero-actions">
              <Link href="/dashboard" className="button lp-btn-lg lp-btn-lime">
                Review work queue
              </Link>
              <Link href="/workflows/new" className="button lp-btn-lg lp-btn-ghost-dark">
                Start a workflow
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
