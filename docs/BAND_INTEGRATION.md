# Band Integration

Band is the visible collaboration and audit layer. Each workflow creates or reuses a room, posts the workflow goal and assignments, receives agent status/finding messages, and publishes the final summary. Message metadata is mirrored into `band_messages`.

`BandClient` is the adapter contract:

- `MockBandClient` creates local IDs and logs clearly labeled mock messages.
- `BandSDKClient` will wrap the real SDK and must fail as unconfigured until implemented.

The backend chooses a client from `BAND_MODE`. No caller should branch on SDK details.

## Live coordinator (`@ATower Coordinator`)

The FastAPI process does **not** keep a Band connection open. Replying to room
mentions requires a long-lived process that holds a WebSocket and calls
`agent.run()`. That process is `apps/api/band/coordinator.py`, shipped as the
`band-agent` Docker Compose service.

It uses the official Band SDK (`band-sdk[langgraph]`, imported as `thenvoi`):

- `ChatOpenAI` (langchain-openai) pointed at Featherless (`FEATHERLESS_BASE_URL`).
- `LangGraphAdapter(llm=..., checkpointer=InMemorySaver(), custom_section=...)`
  with ATower-specific instructions.
- `Agent.create(adapter=..., agent_id=..., api_key=..., ws_url=..., rest_url=...)`
  then `await agent.run()`.

**Honesty contract:** the coordinator can chat and coordinate, but HR workflow
execution is not implemented (`/workflows/{id}/run` returns 501). Its instructions
forbid claiming a screening/retrieval/decision happened; it directs users to create
the workflow and upload artifacts instead.

### Live setup

1. In `.env`, set:
   - `BAND_MODE=sdk`
   - `BAND_AGENT_ID` and `BAND_API_KEY` (the remote agent's credentials)
   - `FEATHERLESS_API_KEY` and a tool-capable model via `FEATHERLESS_TOOL_MODEL`
     (falls back to `FEATHERLESS_DEFAULT_MODEL`). The Band adapter replies via
     platform tools, so the model **must support OpenAI tool calling** — verify
     this for your chosen Featherless model or the agent will stay silent.
   - Optionally `THENVOI_WS_URL` / `THENVOI_REST_URL` (defaults:
     `wss://app.band.ai/api/v1/socket/websocket` and `https://app.band.ai/`).
2. Add the remote agent as a **participant** in the target Band room. The SDK only
   receives messages when the agent is a participant and is mentioned.
3. `docker compose up --build` — the `band-agent` service starts automatically and
   waits for the API to be healthy.

### Troubleshooting

- Watch logs: `docker compose logs -f band-agent`.
- No reply to a mention? Confirm `BAND_MODE=sdk`, the agent is a room participant,
  the mention targets this agent, and the model is tool-capable.
- Config errors (missing creds / non-`sdk` mode) fail fast at startup with an
  explicit message naming the missing variable.

> `BandSDKClient` (the in-process, request-scoped poster) remains intentionally
> unimplemented and raises `NotImplementedError`. The live path is the coordinator
> process, not that client.

