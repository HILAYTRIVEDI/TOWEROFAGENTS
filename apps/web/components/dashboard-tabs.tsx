"use client";

import Link from "next/link";
import { useId, useMemo, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import type { Workflow, WorkflowStatus } from "@/lib/types";

type DomainKey = "hr" | "cto" | "ceo" | "engineering" | "sales";

interface DomainTab {
  key: DomainKey;
  label: string;
  templateSlug: string | null;
}

const DOMAIN_TABS: DomainTab[] = [
  { key: "hr", label: "HR", templateSlug: "hr-candidate-screening" },
  { key: "cto", label: "CTO", templateSlug: null },
  { key: "ceo", label: "CEO", templateSlug: null },
  {
    key: "engineering",
    label: "Engineering",
    templateSlug: "engineering-change-review",
  },
  { key: "sales", label: "Sales", templateSlug: "sales-lead-qualification" },
];

const STATUS_LABELS: Record<WorkflowStatus, string> = {
  draft: "Draft",
  indexing: "Indexing",
  ready: "Ready",
  running: "Running",
  awaiting_review: "Awaiting review",
  completed: "Completed",
  failed: "Failed",
};

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function countByStatus(workflows: Workflow[]): Partial<Record<WorkflowStatus, number>> {
  const counts: Partial<Record<WorkflowStatus, number>> = {};
  for (const workflow of workflows) {
    counts[workflow.status] = (counts[workflow.status] ?? 0) + 1;
  }
  return counts;
}

function WorkflowList({
  createHref = "/workflows/new",
  workflows,
}: {
  createHref?: string;
  workflows: Workflow[];
}) {
  if (workflows.length === 0) {
    return (
      <EmptyState
        actionHref={createHref}
        title="No workflows in this domain yet"
      >
        Workflow records for this domain will appear here once created from
        the workflow library.
      </EmptyState>
    );
  }

  return (
    <ul className="workflow-list">
      {workflows.map((workflow) => (
        <li className="workflow-row" key={workflow.id}>
          <div>
            <p className="workflow-row-title">
              <Link href={`/workflows/${workflow.id}`}>{workflow.title}</Link>
            </p>
            <p className="workflow-row-meta">
              Created {formatDate(workflow.created_at)}
            </p>
          </div>
          <span className={`status-badge status-${workflow.status}`}>
            {STATUS_LABELS[workflow.status]}
          </span>
        </li>
      ))}
    </ul>
  );
}

function ProcessActivityPanel({
  createHref = "/workflows/new",
  label,
}: {
  createHref?: string;
  label: string;
}) {
  return (
    <section aria-label="Process activity">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Process activity</p>
          <h2>Agent findings &amp; Band audit</h2>
        </div>
      </div>
      <EmptyState
        actionHref={createHref}
        title="Live activity feed pending backend runtime"
      >
        {label} Run execution, agent findings, and Band audit messages will
        appear here once the workflow run endpoints are implemented.
      </EmptyState>
    </section>
  );
}

function DomainMetricStrip({
  total,
  statusCounts,
}: {
  total: number;
  statusCounts: Partial<Record<WorkflowStatus, number>>;
}) {
  const inProgress =
    (statusCounts.running ?? 0) +
    (statusCounts.indexing ?? 0) +
    (statusCounts.awaiting_review ?? 0);
  const completed = statusCounts.completed ?? 0;
  const failed = statusCounts.failed ?? 0;

  return (
    <section className="metric-grid" aria-label="Domain metrics">
      <article className="metric-card">
        <span>Total workflows</span>
        <strong>{total}</strong>
        <small>All statuses</small>
      </article>
      <article className="metric-card">
        <span>In progress</span>
        <strong>{inProgress}</strong>
        <small>Indexing, running, or awaiting review</small>
      </article>
      <article className="metric-card">
        <span>Completed / Failed</span>
        <strong>
          {completed} / {failed}
        </strong>
        <small>Resolved outcomes</small>
      </article>
    </section>
  );
}

function HrEngineeringSalesPanel({
  domainLabel,
  templateSlug,
  workflows,
}: {
  domainLabel: string;
  templateSlug: string;
  workflows: Workflow[];
}) {
  const statusCounts = useMemo(() => countByStatus(workflows), [workflows]);
  const createHref = `/workflows/new?template_slug=${encodeURIComponent(templateSlug)}`;

  return (
    <>
      <DomainMetricStrip total={workflows.length} statusCounts={statusCounts} />
      <section>
        <div className="section-heading">
          <div>
            <p className="eyebrow">{domainLabel} workflows</p>
            <h2>Workflow records</h2>
          </div>
        </div>
        <WorkflowList workflows={workflows} createHref={createHref} />
      </section>
      <ProcessActivityPanel
        createHref={createHref}
        label={`${domainLabel} agent findings are not yet wired to a live runtime.`}
      />
    </>
  );
}

function CtoPanel({ engineeringWorkflows }: { engineeringWorkflows: Workflow[] }) {
  const statusCounts = useMemo(
    () => countByStatus(engineeringWorkflows),
    [engineeringWorkflows]
  );

  return (
    <>
      <DomainMetricStrip
        total={engineeringWorkflows.length}
        statusCounts={statusCounts}
      />
      <section>
        <div className="section-heading">
          <div>
            <p className="eyebrow">CTO view</p>
            <h2>Engineering rollup</h2>
          </div>
        </div>
        <EmptyState title="Modeling deferred -- shows engineering workflow rollup">
          There is no dedicated CTO data model yet. The metrics above and the
          list below are a read-only summary of Engineering Change Review
          workflows. No technical-decision findings are fabricated.
        </EmptyState>
        <WorkflowList workflows={engineeringWorkflows} />
      </section>
      <ProcessActivityPanel label="CTO-level technical decision tracking is not yet wired to a live runtime." />
    </>
  );
}

function CeoPanel({
  allWorkflows,
  domainCounts,
}: {
  allWorkflows: Workflow[];
  domainCounts: { label: string; count: number }[];
}) {
  const statusCounts = useMemo(() => countByStatus(allWorkflows), [allWorkflows]);

  return (
    <>
      <section className="metric-grid" aria-label="Organization-wide metrics">
        <article className="metric-card">
          <span>Total workflows</span>
          <strong>{allWorkflows.length}</strong>
          <small>Across all domains</small>
        </article>
        {(Object.keys(STATUS_LABELS) as WorkflowStatus[])
          .filter((status) => (statusCounts[status] ?? 0) > 0)
          .map((status) => (
            <article className="metric-card" key={status}>
              <span>{STATUS_LABELS[status]}</span>
              <strong>{statusCounts[status]}</strong>
              <small>Workflow status</small>
            </article>
          ))}
      </section>

      <section>
        <div className="section-heading">
          <div>
            <p className="eyebrow">Exec rollup</p>
            <h2>Workflows by domain</h2>
          </div>
        </div>
        <ul className="domain-count-list">
          {domainCounts.map((entry) => (
            <li key={entry.label}>
              <span>{entry.label}</span>
              <strong>{entry.count}</strong>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <div className="section-heading">
          <div>
            <p className="eyebrow">Pending approvals</p>
            <h2>Awaiting executive sign-off</h2>
          </div>
        </div>
        <EmptyState title="No pending approvals API yet">
          This panel is a placeholder. Pending-approval records have no
          backing endpoint and are not fabricated here.
        </EmptyState>
      </section>

      <ProcessActivityPanel label="Org-wide Band audit and decision metrics are not yet wired to a live runtime." />
    </>
  );
}

export function DashboardTabs({ workflows }: { workflows: Workflow[] }) {
  const [activeTab, setActiveTab] = useState<DomainKey>("hr");
  const baseId = useId();

  const workflowsBySlug = useMemo(() => {
    const map = new Map<string, Workflow[]>();
    for (const workflow of workflows) {
      const slug = workflow.template_slug ?? "unassigned";
      const existing = map.get(slug) ?? [];
      existing.push(workflow);
      map.set(slug, existing);
    }
    return map;
  }, [workflows]);

  const hrWorkflows = workflowsBySlug.get("hr-candidate-screening") ?? [];
  const engineeringWorkflows =
    workflowsBySlug.get("engineering-change-review") ?? [];
  const salesWorkflows = workflowsBySlug.get("sales-lead-qualification") ?? [];

  const domainCounts = [
    { label: "HR Candidate Screening", count: hrWorkflows.length },
    { label: "Engineering Change Review", count: engineeringWorkflows.length },
    { label: "Sales Lead Qualification", count: salesWorkflows.length },
    {
      label: "Unassigned / other",
      count:
        workflows.length -
        hrWorkflows.length -
        engineeringWorkflows.length -
        salesWorkflows.length,
    },
  ];

  function handleKeyDown(event: React.KeyboardEvent<HTMLButtonElement>, index: number) {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") {
      return;
    }
    event.preventDefault();
    const direction = event.key === "ArrowRight" ? 1 : -1;
    const nextIndex =
      (index + direction + DOMAIN_TABS.length) % DOMAIN_TABS.length;
    const nextTab = DOMAIN_TABS[nextIndex];
    setActiveTab(nextTab.key);
    const nextButton = document.getElementById(`${baseId}-tab-${nextTab.key}`);
    nextButton?.focus();
  }

  return (
    <div className="dashboard-tabs">
      <div className="tab-list" role="tablist" aria-label="Domain dashboards">
        {DOMAIN_TABS.map((tab, index) => {
          const isActive = tab.key === activeTab;
          return (
            <button
              aria-controls={`${baseId}-panel-${tab.key}`}
              aria-selected={isActive}
              className={`tab-trigger${isActive ? " active" : ""}`}
              id={`${baseId}-tab-${tab.key}`}
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              onKeyDown={(event) => handleKeyDown(event, index)}
              role="tab"
              tabIndex={isActive ? 0 : -1}
              type="button"
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {DOMAIN_TABS.map((tab) => {
        const isActive = tab.key === activeTab;
        return (
          <div
            aria-labelledby={`${baseId}-tab-${tab.key}`}
            hidden={!isActive}
            id={`${baseId}-panel-${tab.key}`}
            key={tab.key}
            role="tabpanel"
            tabIndex={0}
          >
            {isActive && tab.key === "hr" && (
              <HrEngineeringSalesPanel
                domainLabel="HR"
                templateSlug="hr-candidate-screening"
                workflows={hrWorkflows}
              />
            )}
            {isActive && tab.key === "engineering" && (
              <HrEngineeringSalesPanel
                domainLabel="Engineering"
                templateSlug="engineering-change-review"
                workflows={engineeringWorkflows}
              />
            )}
            {isActive && tab.key === "sales" && (
              <HrEngineeringSalesPanel
                domainLabel="Sales"
                templateSlug="sales-lead-qualification"
                workflows={salesWorkflows}
              />
            )}
            {isActive && tab.key === "cto" && (
              <CtoPanel engineeringWorkflows={engineeringWorkflows} />
            )}
            {isActive && tab.key === "ceo" && (
              <CeoPanel allWorkflows={workflows} domainCounts={domainCounts} />
            )}
          </div>
        );
      })}
    </div>
  );
}
