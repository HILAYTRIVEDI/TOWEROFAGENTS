# Band Integration

Band is the visible collaboration and audit layer. Each workflow can use its own
room, or fall back to `BAND_DEFAULT_ROOM_ID`. HR screening runs post one concise
specialist finding message per executed agent and mirror the metadata into
`band_messages`.

`BandClient` is the adapter contract:

- `MockBandClient` creates local IDs and logs clearly labeled mock messages.
- `BandSDKClient` makes real Band REST calls (X-API-Key auth). Raises `RuntimeError` at
  construction when `BAND_API_KEY` or `BAND_AGENT_ID` are unset.

The generic `BandClient` remains the room/generic-message adapter. Workflow-run
audit posting uses `band.run_audit.WorkflowRoomAuditor` instead because each
specialist message must be sent under that specialist's own Band API key.

## Workflow run audit

`POST /workflows/{id}/run` executes the HR candidate-screening specialists,
persists the review report, then posts a conversational audit into Band when a
room is available:

1. Room selection is `workflow.band_room_id` first, then `BAND_DEFAULT_ROOM_ID`.
2. The poster sends one message per executed specialist finding, in run order.
3. Each non-final specialist @mentions the next executed specialist.
4. The final specialist @mentions `BAND_REVIEWER_HANDLE` when set, otherwise the
   coordinator (`BAND_AGENT_ID`) or first executed specialist.
5. Every posted/skipped/failed message is persisted to `band_messages` with
   `sender_type='agent'`, `sender_ref=<agent slug>`, `content`, mentions, and
   sanitized raw payload.

Mode semantics are intentionally honest:

| Mode | Meaning |
|---|---|
| `real` | `BAND_MODE=sdk`, specialist credentials exist, and Band returned HTTP 2xx. `band_message_id` is populated when Band returns one. |
| `mock` | `BAND_MODE` is not `sdk`, or that specialist has no credentials. No network call is made. |
| `skipped` | No room ID was supplied to the poster. No network call is made. |
| `failed` | Band/network returned an error. The workflow run still completes and the failed audit row is persisted honestly. |

Band audit failure must never flip a workflow run to `failed`; the report payload
records a `band_audit` summary with counts by mode.

### Separate discussion sessions

Each workflow can have its own Band discussion room/session. Operators can paste
an existing Band room ID during workflow creation or on the workflow detail page.
The next workflow run posts the process discussion and decision handoff into that
room instead of the shared default.

The backend endpoint is `POST /workflows/{id}/band-session`:

- `{ "band_room_id": "..." }` assigns an existing real Band room/session.
- `{ "create_mock_session": true }` behaviour depends on `BAND_MODE`:
  - `BAND_MODE=mock` — creates a local mock room (no network call).
  - `BAND_MODE=sdk` + credentials present — calls `POST /api/v1/agent/chats` on
    Band's REST API via `BandSDKClient`, stores the returned room ID, and uses it
    for all subsequent run audit posts. This is the automatic real room creation path.
  - `BAND_MODE=sdk` + credentials absent — returns HTTP 503 with an explicit message
    naming the missing variables. Never silently falls back to mock.

**Canary:** The `create_room()` request body field and the exact endpoint path are
inferred from Band Agent API naming conventions and must be verified against Band's
live API when credentials are available. A live 422 response during development
indicated the body shape is wrong; correct it once the API contract is confirmed.

## Live agents

The FastAPI process does **not** keep a Band connection open. Replying to room
mentions requires a long-lived process that holds a WebSocket and calls
`agent.run()`. The `band-agent` Docker Compose service runs
`apps/api/band/remote_agents.py`, which supervises the coordinator and every
configured specialist. `apps/api/band/coordinator.py` owns the shared SDK
construction and coordinator behavior.

It uses the official Band SDK (`band-sdk[langgraph]`, imported as `thenvoi`):

- `ChatOpenAI` (langchain-openai) pointed at AIML API as the configured
  OpenAI-compatible provider.
- `LangGraphAdapter(llm=..., checkpointer=InMemorySaver(), custom_section=...)`
  with ATower-specific instructions.
- `Agent.create(adapter=..., agent_id=..., api_key=..., ws_url=..., rest_url=...)`
  then `await agent.run()`.

**Honesty contract:** the coordinator can chat and coordinate, but the API run
path is the source of truth for HR screening execution. Remote agents must not
claim a workflow ran unless `/workflows/{id}/run` actually completed it. Mock
posts are labelled as mock and failed posts are labelled as failed.

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
   - `LLM_PROVIDER=aiml`, `AIML_API_KEY`, and `AIML_DEFAULT_MODEL`.
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
4. Ensure the coordinator, reviewer, and every specialist expected to receive
   mentions are participants in `BAND_DEFAULT_ROOM_ID` or the workflow room.
   Band returns errors such as `422` when a mentioned agent is not in the room;
   those are recorded as `failed` audit messages without failing the workflow.
5. `docker compose up --build` — the `band-agent` service starts automatically,
   waits for the API to be healthy, and runs all configured identities concurrently.

### Troubleshooting

- Watch logs: `docker compose logs -f band-agent`.
- No reply to a mention? Confirm `BAND_MODE=sdk`, the agent is a room participant,
  the mention targets this agent, and the model is tool-capable.
- Config errors (missing coordinator creds, partial specialist pairs, or non-`sdk`
  mode) fail fast at startup with an
  explicit message naming the missing variable.

`BandSDKClient` is now implemented as the in-process, request-scoped REST client.
It handles room creation (`create_room`) and generic message posting (`post_message`)
using `X-API-Key` auth. The injectable `http_post` parameter makes it testable without
network access. The long-lived coordinator/specialist WebSocket connection remains the
concern of the remote-agent supervisor process (`band/remote_agents.py`, `band/coordinator.py`),
not this client.
