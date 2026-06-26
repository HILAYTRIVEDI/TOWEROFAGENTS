"use client";

import Link from "next/link";
import { useState, useEffect, useRef } from "react";

/* ── Animated Node Graph Component ── */
function NodeGraph() {
  const [activeNode, setActiveNode] = useState(0);
  const nodes = [
    { id: "intake", label: "Data Intake", x: 50, y: 30 },
    { id: "parser", label: "Doc Parser", x: 180, y: 80 },
    { id: "embedder", label: "Embedder", x: 310, y: 40 },
    { id: "policy", label: "Policy Guardian", x: 180, y: 180 },
    { id: "bias", label: "Bias Reviewer", x: 330, y: 160 },
    { id: "synthesizer", label: "Synthesizer", x: 460, y: 110 },
    { id: "gate", label: "HITL Gate", x: 520, y: 200 },
  ];

  const edges = [
    [0, 1],
    [1, 2],
    [1, 3],
    [2, 5],
    [3, 4],
    [4, 5],
    [5, 6],
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveNode((prev) => (prev + 1) % nodes.length);
    }, 1800);
    return () => clearInterval(timer);
  }, [nodes.length]);

  return (
    <svg
      viewBox="0 0 600 250"
      className="toa-node-graph"
      aria-label="Live agent orchestration node graph"
    >
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <linearGradient id="edgeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#0ff5" />
          <stop offset="100%" stopColor="#0f96" />
        </linearGradient>
      </defs>

      {/* Edges */}
      {edges.map(([from, to], i) => {
        const f = nodes[from];
        const t = nodes[to];
        const isActive =
          activeNode === from ||
          activeNode === to;
        return (
          <line
            key={`e-${i}`}
            x1={f.x + 40}
            y1={f.y + 16}
            x2={t.x + 40}
            y2={t.y + 16}
            stroke={isActive ? "#00ffc8" : "#ffffff12"}
            strokeWidth={isActive ? 2.5 : 1}
            filter={isActive ? "url(#glow)" : undefined}
            className={isActive ? "toa-edge-pulse" : ""}
          />
        );
      })}

      {/* Nodes */}
      {nodes.map((node, i) => {
        const isActive = activeNode === i;
        return (
          <g key={node.id}>
            <rect
              x={node.x}
              y={node.y}
              width={80}
              height={32}
              rx={8}
              fill={isActive ? "#00ffc820" : "#ffffff08"}
              stroke={isActive ? "#00ffc8" : "#ffffff20"}
              strokeWidth={isActive ? 2 : 1}
              filter={isActive ? "url(#glow)" : undefined}
              className={isActive ? "toa-node-active" : ""}
            />
            <text
              x={node.x + 40}
              y={node.y + 20}
              textAnchor="middle"
              fill={isActive ? "#00ffc8" : "#ffffff80"}
              fontSize="9"
              fontWeight={isActive ? "700" : "500"}
              fontFamily="Inter, sans-serif"
            >
              {node.label}
            </text>
            {isActive && (
              <circle
                cx={node.x + 6}
                cy={node.y + 6}
                r={4}
                fill="#00ffc8"
                filter="url(#glow)"
                className="toa-status-dot"
              />
            )}
          </g>
        );
      })}
    </svg>
  );
}

/* ── Dashboard Mock Component ── */
function DashboardMock() {
  const stages = [
    { name: "Intake Parser", status: "complete" },
    { name: "Role Matcher", status: "complete" },
    { name: "Policy Guardian", status: "complete" },
    { name: "Bias Reviewer", status: "active" },
    { name: "Gap Analyst", status: "pending" },
    { name: "Interview Planner", status: "pending" },
    { name: "Synthesizer", status: "pending" },
    { name: "HITL Gate", status: "pending" },
    { name: "Decision Packet", status: "pending" },
  ];

  return (
    <div className="toa-dash-mock">
      <div className="toa-dash-titlebar">
        <div className="toa-dash-dots">
          <span className="toa-dot toa-dot--r" />
          <span className="toa-dot toa-dot--y" />
          <span className="toa-dot toa-dot--g" />
        </div>
        <span className="toa-dash-title">
          HR Candidate Screening — Live Run
        </span>
      </div>
      <div className="toa-dash-body">
        <div className="toa-dash-sidebar-mock">
          <span className="toa-dash-nav-item toa-dash-nav-active">
            Workflows
          </span>
          <span className="toa-dash-nav-item">Agents</span>
          <span className="toa-dash-nav-item">Knowledge</span>
          <span className="toa-dash-nav-item">Audit Log</span>
        </div>
        <div className="toa-dash-main">
          <div className="toa-dash-header-row">
            <span className="toa-dash-pipeline-label">Pipeline Stages</span>
            <span className="toa-live-badge">
              <span className="toa-live-dot" />
              LIVE
            </span>
          </div>
          <ul className="toa-dash-stage-list">
            {stages.map((s) => (
              <li key={s.name} className={`toa-dash-stage toa-stage-${s.status}`}>
                <span className="toa-stage-indicator">
                  {s.status === "complete"
                    ? "✓"
                    : s.status === "active"
                    ? "▶"
                    : "○"}
                </span>
                <span className="toa-stage-name">{s.name}</span>
                <span className={`toa-stage-badge toa-stage-badge--${s.status}`}>
                  {s.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

/* ── Architecture Diagram Component ── */
function ArchitectureDiagram() {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  const archNodes = [
    {
      id: "nextjs",
      label: "Next.js UI",
      sub: "Dashboard & HITL Gates",
      col: 0,
    },
    {
      id: "fastapi",
      label: "FastAPI / LangGraph Conductor",
      sub: "Orchestration & Proxy",
      col: 1,
    },
    {
      id: "supabase",
      label: "Supabase Vault / pgvector",
      sub: "Secure Embeddings Store",
      col: 2,
    },
    {
      id: "mesh",
      label: "Multi-Framework Agent Mesh",
      sub: "LangChain • AutoGen • CrewAI",
      col: 1,
      row: 1,
    },
  ];

  return (
    <div className="toa-arch-diagram" role="img" aria-label="System architecture flow diagram">
      <div className="toa-arch-top-row">
        {archNodes.slice(0, 3).map((node, i) => (
          <div key={node.id} className="toa-arch-row-segment">
            <div
              className={`toa-arch-box ${
                hoveredNode === node.id ? "toa-arch-box--lit" : ""
              }`}
              onMouseEnter={() => setHoveredNode(node.id)}
              onMouseLeave={() => setHoveredNode(null)}
            >
              <span className="toa-arch-box-label">{node.label}</span>
              <span className="toa-arch-box-sub">{node.sub}</span>
            </div>
            {i < 2 && (
              <div
                className={`toa-arch-connector ${
                  hoveredNode === archNodes[i].id ||
                  hoveredNode === archNodes[i + 1].id
                    ? "toa-arch-connector--lit"
                    : ""
                }`}
              >
                <span className="toa-arch-proto">
                  {i === 0 ? "API" : "gRPC"}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="toa-arch-vertical">
        <div
          className={`toa-arch-vline ${
            hoveredNode === "fastapi" || hoveredNode === "mesh"
              ? "toa-arch-vline--lit"
              : ""
          }`}
        />
        <span
          className={`toa-arch-proxy-label ${
            hoveredNode === "fastapi" || hoveredNode === "mesh"
              ? "toa-arch-proxy-label--lit"
              : ""
          }`}
        >
          Secure RPC Proxy
        </span>
      </div>

      <div
        className={`toa-arch-box toa-arch-box--mesh ${
          hoveredNode === "mesh" ? "toa-arch-box--lit" : ""
        }`}
        onMouseEnter={() => setHoveredNode("mesh")}
        onMouseLeave={() => setHoveredNode(null)}
      >
        <span className="toa-arch-box-label">Multi-Framework Agent Mesh</span>
        <span className="toa-arch-box-sub">
          LangChain • AutoGen • CrewAI Nodes
        </span>
      </div>
    </div>
  );
}

/* ── Workflow Card Expand Component ── */
function WorkflowCards() {
  const [expandedCard, setExpandedCard] = useState<number | null>(null);

  const cards = [
    {
      title: "HR Candidate Screening",
      badge: "LIVE IN SANDBOX",
      badgeClass: "toa-badge--live",
      desc: "Ingests resumes, matches job descriptions against organizational policies, and strings together 9 isolated agent roles (e.g., Bias Reviewer, Interview Planner) to construct verified talent packets.",
      code: `POST /workflows/{id}/run

// Immutable Decision Payload
{
  "recommendation": "ADVANCE_TO_INTERVIEW",
  "confidence": 0.87,
  "strengths": [
    "5yr distributed systems experience",
    "Strong OSS contributions"
  ],
  "gaps": [
    "No healthcare domain exposure"
  ],
  "policy_note": "Passes DEI bias review — no disqualifying flags",
  "audit_hash": "sha256:9f86d0..."
}`,
    },
    {
      title: "Procurement & Finance Approvals",
      badge: "TEMPLATE",
      badgeClass: "toa-badge--template",
      desc: "Validates invoices, cross-references purchase orders, and evaluates spending thresholds against strict corporate bylaws.",
      code: null,
    },
    {
      title: "Engineering Change Reviews",
      badge: "TEMPLATE",
      badgeClass: "toa-badge--template",
      desc: "Cross-checks codebase pull requests against security protocols, internal dependency trees, and structural guidelines.",
      code: null,
    },
  ];

  return (
    <div className="toa-workflow-grid">
      {cards.map((card, i) => (
        <article
          key={i}
          className={`toa-workflow-card ${
            expandedCard === i ? "toa-workflow-card--expanded" : ""
          } ${i === 0 ? "toa-workflow-card--primary" : ""}`}
          onClick={() => setExpandedCard(expandedCard === i ? null : i)}
        >
          <span className={`toa-wf-badge ${card.badgeClass}`}>
            {i === 0 && <span className="toa-pulse-dot" />}
            {card.badge}
          </span>
          <h3 className="toa-wf-title">{card.title}</h3>
          <p className="toa-wf-desc">{card.desc}</p>
          {card.code && (
            <div
              className={`toa-wf-code-block ${
                expandedCard === i ? "toa-wf-code-block--visible" : ""
              }`}
            >
              <div className="toa-code-header">
                <span>api-contract.json</span>
                <span className="toa-code-lang">JSON</span>
              </div>
              <pre>
                <code>{card.code}</code>
              </pre>
            </div>
          )}
          {i === 0 && (
            <span className="toa-wf-expand-hint">
              {expandedCard === 0
                ? "Click to collapse"
                : "Click to inspect API contract"}
            </span>
          )}
        </article>
      ))}
    </div>
  );
}

/* ── Typing Terminal Component ── */
function Terminal() {
  const [lines, setLines] = useState<string[]>([]);
  const termRef = useRef<HTMLDivElement>(null);

  const allLines = [
    "$ git clone github.com/your-repo/tower-of-agents",
    "Cloning into 'tower-of-agents'...",
    "remote: Enumerating objects: 1,247, done.",
    "remote: Compressing objects: 100% (891/891), done.",
    "",
    "$ cd tower-of-agents",
    "",
    "$ docker compose up --build",
    "[+] Building 24.3s (18/18) FINISHED",
    " => [fastapi] Building Dockerfile...",
    " => [nextjs] Building Dockerfile...",
    " => [supabase] Pulling postgres:15...",
    " => [pgvector] Installing extensions...",
    "[+] Running 4/4",
    " ✔ Container toa-supabase    Started    0.8s",
    " ✔ Container toa-pgvector    Started    1.2s",
    " ✔ Container toa-fastapi     Started    2.1s",
    " ✔ Container toa-nextjs      Started    2.4s",
    "",
    "🟢 All services healthy. Dashboard → http://localhost:3000",
  ];

  useEffect(() => {
    let i = 0;
    const timer = setInterval(() => {
      if (i < allLines.length) {
        const currentLine = allLines[i];
        i++;
        setLines((prev) => [...prev, currentLine]);
        if (termRef.current) {
          termRef.current.scrollTop = termRef.current.scrollHeight;
        }
      } else {
        clearInterval(timer);
      }
    }, 220);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="toa-terminal" ref={termRef}>
      <div className="toa-terminal-titlebar">
        <div className="toa-dash-dots">
          <span className="toa-dot toa-dot--r" />
          <span className="toa-dot toa-dot--y" />
          <span className="toa-dot toa-dot--g" />
        </div>
        <span className="toa-terminal-path">~/tower-of-agents</span>
      </div>
      <div className="toa-terminal-body">
        {lines.map((line, i) => (
          <div
            key={i}
            className={`toa-term-line ${
              line.startsWith("$") ? "toa-term-cmd" : ""
            } ${line.startsWith(" ✔") ? "toa-term-success" : ""} ${
              line.startsWith("🟢") ? "toa-term-healthy" : ""
            }`}
          >
            {line}
          </div>
        ))}
        <span className="toa-cursor">▌</span>
      </div>
    </div>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   MAIN LANDING PAGE
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function LandingPage() {
  return (
    <>
      {/* ── Top bar ── */}
      <header className="toa-topbar" role="banner">
        <Link href="/" className="toa-topbar-brand" aria-label="Tower of Agents home">
          <span className="toa-brand-mark" aria-hidden="true">
            T
          </span>
          <span className="toa-brand-wordmark">Tower of Agents</span>
        </Link>
        <nav aria-label="Site navigation" className="toa-topbar-nav">
          <Link href="/docs" className="toa-nav-link">
            Docs
          </Link>
          <Link href="/agents" className="toa-nav-link">
            Agents
          </Link>
          <Link href="/dashboard" className="toa-nav-link toa-nav-cta">
            Open Dashboard
          </Link>
        </nav>
      </header>

      <main>
        {/* ━━━ Section 1: Hero / Above the Fold ━━━ */}
        <section className="toa-hero" aria-labelledby="hero-heading">
          {/* Background grid effect */}
          <div className="toa-hero-grid" aria-hidden="true" />
          <div className="toa-hero-glow" aria-hidden="true" />

          <div className="toa-hero-inner">
            <div className="toa-hero-copy">
              <p className="toa-eyebrow">
                Enterprise Agent Governance &amp; Control Plane
              </p>
              <h1 id="hero-heading">
                The Unified Governance &amp; Execution Layer for Enterprise AI
                Agents.
              </h1>
              <p className="toa-lede">
                Move past chaotic, unconstrained agent chatrooms. Secure, audit,
                and orchestrate your autonomous digital workforce with a
                deterministic state-machine operating system.
              </p>
              <div className="toa-hero-actions">
                <Link href="/dashboard" className="toa-btn toa-btn--primary">
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 18 18"
                    fill="none"
                    aria-hidden="true"
                  >
                    <rect
                      x="2"
                      y="2"
                      width="14"
                      height="14"
                      rx="3"
                      stroke="currentColor"
                      strokeWidth="1.5"
                    />
                    <path
                      d="M7 6l4 3-4 3V6z"
                      fill="currentColor"
                    />
                  </svg>
                  Deploy Local Sandbox (Docker)
                </Link>
                <Link href="/docs" className="toa-btn toa-btn--ghost">
                  Book a Technical Demo
                </Link>
              </div>
            </div>

            <div className="toa-hero-visual">
              <div className="toa-split-pane">
                <div className="toa-pane toa-pane--left">
                  <div className="toa-pane-label">Frontend Dashboard</div>
                  <DashboardMock />
                </div>
                <div className="toa-pane-divider" />
                <div className="toa-pane toa-pane--right">
                  <div className="toa-pane-label">
                    LangGraph State Machine
                  </div>
                  <NodeGraph />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ━━━ Section 2: The Core Problem — Contrast Matrix ━━━ */}
        <section
          className="toa-section toa-problem-section"
          aria-labelledby="problem-heading"
        >
          <div className="toa-section-inner">
            <p className="toa-eyebrow">The Agent Interoperability Crisis</p>
            <h2 id="problem-heading" className="toa-section-title">
              The Agent Interoperability Crisis.
            </h2>
            <p className="toa-section-lede">
              Unconstrained agent communication creates a compliance black box,
              infinite loops, and data leaks. TOA enforces strict operational
              guardrails.
            </p>

            <div className="toa-contrast-table" role="table">
              <div className="toa-contrast-header" role="row">
                <div
                  className="toa-contrast-cell toa-contrast-cell--chaos"
                  role="columnheader"
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 20 20"
                    fill="none"
                    aria-hidden="true"
                  >
                    <circle
                      cx="10"
                      cy="10"
                      r="8"
                      stroke="#ff4d4d"
                      strokeWidth="1.5"
                    />
                    <path
                      d="M7 7l6 6M13 7l-6 6"
                      stroke="#ff4d4d"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    />
                  </svg>
                  The Current Chaos
                  <span className="toa-contrast-sub">
                    Ungoverned Agent Chat
                  </span>
                </div>
                <div
                  className="toa-contrast-cell toa-contrast-cell--toa"
                  role="columnheader"
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 20 20"
                    fill="none"
                    aria-hidden="true"
                  >
                    <circle
                      cx="10"
                      cy="10"
                      r="8"
                      stroke="#00ffc8"
                      strokeWidth="1.5"
                    />
                    <path
                      d="M6 10l3 3 5-6"
                      stroke="#00ffc8"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  The TOA Standard
                  <span className="toa-contrast-sub">
                    State-Governed Execution
                  </span>
                </div>
              </div>

              {[
                {
                  chaos:
                    "Infinite Agent Ping-Pong: Agents message back-and-forth endlessly across framework boundaries, ballooning token costs.",
                  toa: "Deterministic Boundaries: LangGraph state machines dictate exactly when and who is allowed to speak next.",
                },
                {
                  chaos:
                    "The Compliance Black Box: No immutable or verifiable legal paper trail of why agents made a critical corporate decision.",
                  toa: "Auditable Decision Packets: Cryptographically isolated audit logs capture raw machine debate, requiring human-in-the-loop sign-off.",
                },
                {
                  chaos:
                    "Data Payload Bottlenecks: Massive raw data strings passed directly into chat rooms, breaking context limits and leaking access.",
                  toa: "Pointer-Based RAG Ingestion: Secure metadata pointers link to protected pgvector infrastructure without exposing core records.",
                },
              ].map((row, i) => (
                <div className="toa-contrast-row" role="row" key={i}>
                  <div
                    className="toa-contrast-cell toa-contrast-cell--chaos"
                    role="cell"
                  >
                    {row.chaos}
                  </div>
                  <div
                    className="toa-contrast-cell toa-contrast-cell--toa"
                    role="cell"
                  >
                    {row.toa}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ━━━ Section 3: Architecture — How it Works ━━━ */}
        <section
          className="toa-section toa-arch-section"
          aria-labelledby="arch-heading"
        >
          <div className="toa-section-inner">
            <p className="toa-eyebrow">Under the Hood</p>
            <h2 id="arch-heading" className="toa-section-title">
              Under the Hood of the AI Operating System.
            </h2>
            <p className="toa-section-lede">
              A three-step secure pipeline moving from unstructured company data
              to fully audited execution.
            </p>

            <div className="toa-steps-row">
              {[
                {
                  num: "01",
                  title: "Ingest & Scope",
                  desc: "Upload enterprise artifacts, hiring policies, or technical guidelines. Text is safely parsed, chunked, and embedded into your isolated pgvector database.",
                },
                {
                  num: "02",
                  title: "Govern & Intercept",
                  desc: "Multi-framework agent meshes (LangChain, AutoGen, CrewAI) execute under a centralized LangGraph runtime. TOA acts as a proxy, dynamically locking and unlocking communication channels thread-by-thread.",
                  tag: "The Proxy Conductor",
                },
                {
                  num: "03",
                  title: "Synthesize & Authorize",
                  desc: "Human-in-the-loop gates freeze high-impact actions until an operator reviews the structured decision packet and verified audit ledger on the Next.js frontend dashboard.",
                },
              ].map((step) => (
                <div className="toa-step-card" key={step.num}>
                  <span className="toa-step-num">{step.num}</span>
                  <h3 className="toa-step-title">
                    {step.title}
                    {step.tag && (
                      <span className="toa-step-tag">{step.tag}</span>
                    )}
                  </h3>
                  <p className="toa-step-desc">{step.desc}</p>
                </div>
              ))}
            </div>

            <ArchitectureDiagram />
          </div>
        </section>

        {/* ━━━ Section 4: Production-Ready Workflows ━━━ */}
        <section
          className="toa-section toa-workflows-section"
          aria-labelledby="workflows-heading"
        >
          <div className="toa-section-inner">
            <p className="toa-eyebrow">Production-Ready</p>
            <h2 id="workflows-heading" className="toa-section-title">
              Built for High-Stakes Operations.
            </h2>
            <p className="toa-section-lede">
              Deploy specialized AI hierarchies into complex corporate
              environments immediately.
            </p>

            <WorkflowCards />
          </div>
        </section>

        {/* ━━━ Section 5: No-Vaporware Technical Footer ━━━ */}
        <section
          className="toa-section toa-infra-section"
          aria-labelledby="infra-heading"
        >
          <div className="toa-section-inner toa-infra-inner">
            <p className="toa-eyebrow">Zero Fluff. Pure Infrastructure.</p>
            <h2 id="infra-heading" className="toa-section-title">
              Zero Fluff. Pure Infrastructure.
            </h2>
            <p className="toa-section-lede">
              Spin up a local, mock-safe instance of the entire environment with
              a single terminal command.
            </p>

            <Terminal />

            <div className="toa-stack-logos">
              <div className="toa-stack-logo">
                <span className="toa-stack-icon">⚡</span>
                <span>FastAPI</span>
              </div>
              <div className="toa-stack-logo">
                <span className="toa-stack-icon">▲</span>
                <span>Next.js</span>
              </div>
              <div className="toa-stack-logo">
                <span className="toa-stack-icon">⬡</span>
                <span>Supabase</span>
              </div>
              <div className="toa-stack-logo">
                <span className="toa-stack-icon">◈</span>
                <span>LangGraph</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="toa-footer" role="contentinfo">
        <div className="toa-footer-inner">
          <div className="toa-footer-brand">
            <span className="toa-brand-mark toa-brand-mark--sm" aria-hidden="true">
              T
            </span>
            <span className="toa-brand-wordmark">Tower of Agents</span>
          </div>
          <nav aria-label="Footer navigation" className="toa-footer-nav">
            <Link href="/dashboard">Dashboard</Link>
            <Link href="/workflows">Workflows</Link>
            <Link href="/agents">Agents</Link>
            <Link href="/knowledge-base">Knowledge Base</Link>
            <Link href="/docs">Docs</Link>
          </nav>
          <p className="toa-footer-note">
            Enterprise agent governance. Deterministic execution. Human-owned decisions.
          </p>
        </div>
      </footer>
    </>
  );
}
