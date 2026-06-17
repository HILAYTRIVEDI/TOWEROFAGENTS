# Band Integration

Band is the visible collaboration and audit layer. Each workflow creates or reuses a room, posts the workflow goal and assignments, receives agent status/finding messages, and publishes the final summary. Message metadata is mirrored into `band_messages`.

`BandClient` is the adapter contract:

- `MockBandClient` creates local IDs and logs clearly labeled mock messages.
- `BandSDKClient` will wrap the real SDK and must fail as unconfigured until implemented.

The backend chooses a client from `BAND_MODE`. No caller should branch on SDK details.

## Live agents

The FastAPI process does **not** keep a Band connection open. Replying to room
mentions requires a long-lived process that holds a WebSocket and calls
`agent.run()`. The `band-agent` Docker Compose service runs
`apps/api/band/remote_agents.py`, which supervises the coordinator and every
configured specialist. `apps/api/band/coordinator.py` owns the shared SDK
construction and coordinator behavior.

It uses the official Band SDK (`band-sdk[langgraph]`, imported as `thenvoi`):

- `ChatOpenAI` (langchain-openai) pointed at the configured OpenAI-compatible
  provider: AIML API when `LLM_PROVIDER=aiml`, otherwise Featherless.
- `LangGraphAdapter(llm=..., checkpointer=InMemorySaver(), custom_section=...)`
  with ATower-specific instructions.
- `Agent.create(adapter=..., agent_id=..., api_key=..., ws_url=..., rest_url=...)`
  then `await agent.run()`.

**Honesty contract:** the coordinator can chat and coordinate, but HR workflow
execution is not implemented (`/workflows/{id}/run` returns 501). Its instructions
forbid claiming a screening/retrieval/decision happened; it directs users to create
the workflow and upload artifacts instead.

The specialist catalog contains:

| Slug | Band role |
|---|---|
| `workflow-router` | Selects a template, required artifacts, and roster |
| `rag-retriever` | Checks evidence availability without fabricating retrieval |
| `policy-guardian` | Reviews supplied policy and escalation needs |
| `final-decision` | Synthesizes advisory, human-reviewed findings |
| `resume-jd-matcher` | Compares job requirements with supplied resume evidence |
| `bias-reviewer` | Audits candidate-screening reasoning for unfair assumptions |
| `interview-planner` | Creates job-related questions for evidence gaps |
| `lead-qualifier` | Reviews ICP/CRM evidence and suggests a follow-up |
| `engineering-reviewer` | Reviews supplied changes, risks, and tests |

### Live setup

1. In `.env`, set:
   - `BAND_MODE=sdk`
   - `BAND_AGENT_ID` and `BAND_API_KEY` (the remote agent's credentials)
   - A tool-capable model provider:
     - `LLM_PROVIDER=aiml`, `AIML_API_KEY`, and `AIML_DEFAULT_MODEL`; or
     - `LLM_PROVIDER=featherless`, `FEATHERLESS_API_KEY`, and a model via
       `FEATHERLESS_TOOL_MODEL` (falls back to `FEATHERLESS_DEFAULT_MODEL`).
     The Band adapter replies via platform tools, so the model **must support
     OpenAI tool calling** or the agent will stay silent.
   - Optionally `THENVOI_WS_URL` / `THENVOI_REST_URL` (defaults:
     `wss://app.band.ai/api/v1/socket/websocket` and `https://app.band.ai/`).
2. Add the remote agent as a **participant** in the target Band room. The SDK only
   receives messages when the agent is a participant and is mentioned.
3. Create each specialist as a separate Band **Remote Agent**, then add its UUID
   and API key using the matching environment prefix. Example:

   ```text
   resume-jd-matcher
     -> BAND_RESUME_JD_MATCHER_AGENT_ID
     -> BAND_RESUME_JD_MATCHER_API_KEY
   ```

   All supported names are listed in `.env.example`. Incomplete pairs fail fast;
   roles with neither value are skipped.
4. `docker compose up --build` — the `band-agent` service starts automatically,
   waits for the API to be healthy, and runs all configured identities concurrently.

### Troubleshooting

- Watch logs: `docker compose logs -f band-agent`.
- No reply to a mention? Confirm `BAND_MODE=sdk`, the agent is a room participant,
  the mention targets this agent, and the model is tool-capable.
- Config errors (missing coordinator creds, partial specialist pairs, or non-`sdk`
  mode) fail fast at startup with an
  explicit message naming the missing variable.

> `BandSDKClient` (the in-process, request-scoped poster) remains intentionally
> unimplemented and raises `NotImplementedError`. The live path is the remote-agent
> supervisor process, not that client.
