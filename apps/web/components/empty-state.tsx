import Link from "next/link";
import type { ReactNode } from "react";

export function EmptyState({
  title,
  actionHref,
  actionIconLabel = "Open create workflow form",
  actionLabel = "Create workflow",
  children,
}: {
  title: string;
  actionHref?: string;
  actionIconLabel?: string;
  actionLabel?: string;
  children: ReactNode;
}) {
  const icon = actionHref ? (
    <Link
      aria-label={actionIconLabel}
      className="empty-icon empty-icon-link"
      href={actionHref}
    >
      +
    </Link>
  ) : (
    <span className="empty-icon" aria-hidden="true">
      +
    </span>
  );

  return (
    <section className="empty-state">
      {icon}
      <h2>{title}</h2>
      <p>{children}</p>
      {actionHref ? (
        <Link className="button primary" href={actionHref}>
          {actionLabel}
        </Link>
      ) : null}
    </section>
  );
}
