import Link from "next/link";

export default function NotFound() {
  return (
    <section className="empty-state">
      <h1>Page not found</h1>
      <p>The requested control-tower view does not exist.</p>
      <Link href="/dashboard">Return to dashboard</Link>
    </section>
  );
}

