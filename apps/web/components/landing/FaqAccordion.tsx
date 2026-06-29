// No "use client" needed — <details>/<summary> is native HTML with no JS required.

const faqs: { q: string; a: string }[] = [
  {
    q: "What is Tower of Agents?",
    a: "Tower of Agents is an AI control tower that turns document-heavy internal workflows into structured, auditable decision packets. Instead of a generic chatbot, it assembles a role-based team of specialist AI agents — Procurement, Finance, Legal, Security, Compliance — each reviewing evidence from your uploaded documents. The result is a recommendation with cited evidence, risk flags, and a human approval step.",
  },
  {
    q: "How is this different from ChatGPT, Copilot, or a generic AI assistant?",
    a: "Generic AI assistants give unstructured answers with no citations, no audit trail, and no human approval gate. Tower of Agents produces a structured decision packet: every claim cites a source, every agent records its finding, disagreements between agents are surfaced, and a human makes the final call. The entire review is logged for compliance.",
  },
  {
    q: "What documents and data sources does it support?",
    a: "TOA supports PDF, DOCX, XLSX, and plain-text uploads today. You can upload vendor contracts, SOC 2 reports, financial statements, HR resumes, policy documents, and engineering specs. The Company Brain module stores your internal context — pricing thresholds, compliance rules, approved vendor lists — so agents review against your standards, not generic ones.",
  },
  {
    q: "Is my data secure? What about confidentiality?",
    a: "Documents are treated as confidential and scoped to your organization. TOA enforces organization-level data isolation, role-based access control, and does not log document contents to external services. The self-hosted and private-cloud deployment option lets you keep all data entirely within your infrastructure.",
  },
  {
    q: "Which AI models does it use?",
    a: "TOA is BYOM-ready (Bring Your Own Model). It ships with routing support for leading providers (OpenAI, Anthropic, and open models via Featherless) and selects the best model per agent task — balancing cost, accuracy, and compliance requirements. You can lock specific models for specific agents if your governance requires it.",
  },
  {
    q: "Can I use my own models or API keys (BYOM / BYOK)?",
    a: "Yes. BYOM and BYOK are core features, not add-ons. You can supply your own OpenAI, Anthropic, or compatible API keys, or point TOA at a self-hosted model endpoint. Model cost is tracked per workflow so you can optimize value per token over time.",
  },
  {
    q: "How long does a typical vendor review take?",
    a: "A full six-agent vendor onboarding review — Procurement, Finance, Legal, Security, Compliance, and Controller — typically completes in 3–8 minutes depending on document volume and model latency. That compares to 2–4 days for a manual review cycle. The decision packet is ready for human approval the moment agents finish.",
  },
  {
    q: "What workflows are available right now?",
    a: "Vendor Onboarding Review and HR Candidate Screening are production-ready today. Contract Review, Policy Exception Review, and Engineering Change Review are in active development and available to design partners. New workflow templates can be configured from the workflow builder without code.",
  },
  {
    q: "How do I get started?",
    a: "The fastest path is the Design Partner program: book a live demo, we configure your first workflow together (usually vendor onboarding or HR screening), and you get dedicated onboarding support. Most pilots are live within one week. Apply via the form on this page or email hilaytrivedi1224@gmail.com.",
  },
];

export default function FaqAccordion() {
  return (
    <dl className="lp-faq-list">
      {faqs.map(({ q, a }, i) => (
        <details key={i} className="lp-faq-item">
          <summary className="lp-faq-question">{q}</summary>
          <div className="lp-faq-answer">
            <p>{a}</p>
          </div>
        </details>
      ))}
    </dl>
  );
}
