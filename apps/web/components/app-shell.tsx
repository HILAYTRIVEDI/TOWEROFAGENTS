import Link from "next/link";
import type { ReactNode } from "react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/workflows", label: "Workflows" },
  { href: "/agents", label: "Agents" },
  { href: "/knowledge-base", label: "Knowledge" },
  { href: "/docs", label: "Docs" },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/dashboard">
          <span className="brand-mark">A</span>
          <span>
            <strong>ATower</strong>
            <small>Agent control plane</small>
          </span>
        </Link>
        <nav aria-label="Primary navigation">
          {NAV_ITEMS.map((item) => (
            <Link key={item.href} href={item.href}>
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="environment">
          <span className="status-dot" aria-hidden="true" />
          Base scaffold
        </div>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  );
}
