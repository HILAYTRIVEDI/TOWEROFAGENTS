import { PageHeader } from "@/components/page-header";

const AGENT_GROUPS = [
  {
    category: "Platform",
    names: [
      "Workflow Router",
      "RAG Retriever",
      "Policy Guardian",
      "Final Decision Agent",
    ],
  },
  {
    category: "HR specialists",
    names: ["Resume/JD Matcher", "Bias/Safety Reviewer", "Interview Planner"],
  },
  {
    category: "Breadth specialists",
    names: ["Lead Qualifier", "Engineering Reviewer"],
  },
] as const;

export default function AgentsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Agent registry"
        title="Specialists with explicit jobs."
        description="The registry mirrors the backend scaffold. Execution, metrics, and live provider status arrive during product development."
      />
      <div className="agent-grid">
        {AGENT_GROUPS.map((group) => (
          <section className="agent-group" key={group.category}>
            <p className="eyebrow">{group.category}</p>
            {group.names.map((name) => (
              <article key={name}>
                <span className="agent-avatar">{name.charAt(0)}</span>
                <div>
                  <h2>{name}</h2>
                  <p>Contract ready · execution pending</p>
                </div>
              </article>
            ))}
          </section>
        ))}
      </div>
    </>
  );
}

