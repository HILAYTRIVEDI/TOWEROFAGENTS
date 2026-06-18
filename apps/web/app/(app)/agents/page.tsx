import { PageHeader } from "@/components/page-header";
import { listAgents } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function AgentsPage() {
  const agents = await listAgents();
  const groups = new Map<string, typeof agents>();
  for (const agent of agents) {
    groups.set(agent.category, [...(groups.get(agent.category) ?? []), agent]);
  }

  return (
    <>
      <PageHeader
        eyebrow="Agent registry"
        title="Specialists with explicit jobs."
        description="This registry is loaded directly from the FastAPI agent catalog."
      />
      <div className="agent-grid">
        {[...groups.entries()].map(([category, categoryAgents]) => (
          <section className="agent-group" key={category}>
            <p className="eyebrow">{category}</p>
            {categoryAgents.map((agent) => (
              <article key={agent.slug}>
                <span className="agent-avatar">{agent.name.charAt(0)}</span>
                <div>
                  <h2>{agent.name}</h2>
                  <p>{agent.description}</p>
                </div>
              </article>
            ))}
          </section>
        ))}
      </div>
    </>
  );
}
