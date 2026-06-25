# Demo Pointers — Band of Agents Hackathon Submission

> Quick reference to include in / alongside the demo. Judges evaluate from the
> demo video even if the live demo later goes offline, so the video must stand
> on its own.

## Submission facts

- **Deadline:** Friday, June 19th — 5:00 PM CEST / 8:00 AM PDT.
- **Submit via:** your team's page on lablab.ai.
- **Who submits:** only the Team Leader can submit the final project.
- **Guidelines:** https://lablab.ai/ai-articles/hackathon-guidelines
- Submit early — traffic spikes near the deadline can cause delays.

## Resources must stay public during judging

Keep everything shared in the submission public and accessible during the
judging period, including the live demo where possible. If the live demo relies
on paid credits, API tokens, or limited infra that may not stay online, the
**video demo is the source of truth** — make it complete.

## The demo video MUST show

1. **The project in action** — a real run, not slides.
2. **Core features and workflows** — end-to-end, the way a judge would use it.
3. **How the agents collaborate** — Band as the visible collaboration and audit
   layer: rooms, @mentions, and the audit trail across agents.
4. **Value and impact** — the problem solved and why this solution matters.

## Tower of Agents — what to highlight on screen

- **Architecture path:** Next.js → FastAPI → Supabase / LangGraph / Band.
- **Band is visible:** show agents posting to rooms and the audit sync, not a
  hidden chat widget. Supabase is the system of record.
- **Honest integrations:** demo real provider calls; never present a mock as a
  real integration. Call out any unconfigured / mock states explicitly.
- **No secrets on screen:** scrub API keys/tokens from terminals, env files, and
  browser tabs before recording.

## Pre-record checklist

- [ ] Live demo reachable, or video covers the full flow if it may go offline.
- [ ] All shared links public and open without login.
- [ ] Agent collaboration in Band clearly visible in the recording.
- [ ] No secrets visible anywhere in the capture.
- [ ] Team Leader has the final assets ready to submit on lablab.ai.
