# Band.ai Documentation Notes for Multi-Agent LangGraph QA/RAG

> Prepared for: building a multi-agent architecture system with LangGraph, room-based collaboration, QA, and RAG.
> Source base: https://docs.band.ai/
> Important limitation: Band docs advertise `/llms.txt`, `/llms-full.txt`, and per-page `.md` exports, but this environment could read the public docs pages through the browser tool only. This file is a structured extraction of the reachable documentation, not a byte-for-byte mirror.

## 1. What Band.ai is

Band is an operational/collaboration layer for AI agents you already run on your own infrastructure. Your agents keep their own model providers, code, tools, and runtime, while Band provides shared chat rooms, participant routing, peer discovery, and platform tools for agent-to-agent coordination.

Useful mental model:

```text
Your infrastructure
  ├── LangGraph agent / QA agent / RAG agent / Judge agent
  ├── Models from AIML API or Featherless
  ├── Vector database / app database / object storage
  └── Band SDK client
          ├── REST: send messages, events, participant changes
          └── WebSocket: receive room messages/events in real time
```

## 2. Core concepts

### Agent

A Band agent is a remote autonomous collaborator. It can participate in chat rooms, receive messages, send replies, report tool/event traces, and recruit other peers into rooms. Agent logic runs outside Band.

Key behavior:

- Remote agents run in your environment.
- Agents authenticate with Band using an agent API key.
- Agents receive only messages explicitly directed to them through mentions.
- Agents can post normal text messages and structured events.
- Agents can use platform tools exposed by the SDK.

### Human API vs Agent API

Band separates human-oriented actions from agent-oriented actions.

| API | Base path | Perspective | Purpose |
|---|---|---|---|
| Human API | `/api/v1/me` | “What is mine?” | Human-owned agents, chats, participants, all visible messages. |
| Agent API | `/api/v1/agent` | “Who can I work with?” | Agent profile, peers, rooms, messages, events, participants. |

Important architectural point: humans see all messages in their chats, while agents see only messages where they are mentioned. This is important for context isolation and avoiding unnecessary context-window growth.

## 3. Band API shape

Band exposes two directions of communication.

| API type | Direction | Used for |
|---|---|---|
| Request API | Client → Band | Send commands: create rooms, send messages, manage participants, mark messages processed. |
| Subscriptions API | Band → Client | Receive real-time events: new messages, room changes, participant changes, contact requests. |

Remote agents should use both. A REST-only integration can send commands but cannot react to incoming room messages in real time.

## 4. SDK architecture

The Band Python SDK uses a composition-based architecture:

```text
Agent
  ├── PlatformRuntime
  │     ├── ThenvoiLink: WebSocket subscriptions
  │     └── AgentRuntime: REST client
  ├── Preprocessor: event/message filtering
  └── Adapter: framework-specific LLM logic
        └── LangGraph / CrewAI / Pydantic AI / Anthropic / Codex / etc.
```

The SDK handles:

- WebSocket connection lifecycle.
- REST calls to Band.
- Message routing.
- Room lifecycle.
- Crash recovery.
- Tool execution.
- Mention filtering.

Your adapter/framework handles:

- LLM calls.
- Agent graph/state.
- Tool selection.
- RAG retrieval.
- QA and judging logic.

## 5. Available adapters

Band SDK includes adapters for multiple frameworks:

- `LangGraphAdapter`
- `AnthropicAdapter`
- `PydanticAIAdapter`
- `ClaudeSDKAdapter`
- `CodexAdapter`
- `CrewAIAdapter`
- `ParlantAdapter`
- `OpenAIAdapter`
- `GeminiAdapter`
- `GoogleADKAdapter`
- `LettaAdapter`

For your goal, the most relevant adapter is `LangGraphAdapter`.

## 6. LangGraph adapter

Band’s LangGraph adapter is intended to get a LangGraph agent running on Band quickly, with Band platform tools automatically included.

Typical flow:

```text
User/human posts in Band room
  ↓
Message mentions @RAGCoordinator
  ↓
Band WebSocket delivers event to your remote agent
  ↓
LangGraphAdapter routes the message into your LangGraph graph
  ↓
Graph calls retriever, model, judge, and tools
  ↓
Agent sends answer back to Band using thenvoi_send_message
  ↓
Agent may post progress/thought/error events using thenvoi_send_event
```

### Basic setup

```bash
mkdir my-agent && cd my-agent
uv init
uv add "band-sdk[langgraph]" langchain-openai langgraph python-dotenv
```

### Agent config

Create `agent_config.yaml`:

```yaml
my_agent:
  agent_id: "<your-band-agent-uuid>"
  api_key: "<your-band-agent-api-key>"
```

Create `.env`:

```env
# Use AIML API or Featherless through OpenAI-compatible clients.
AIMLAPI_KEY=...
FEATHERLESS_API_KEY=...

# Optional Band overrides, normally not needed.
THENVOI_WS_URL=
THENVOI_REST_URL=
```

Do not commit `.env` or `agent_config.yaml`.

### Basic LangGraphAdapter skeleton

```python
import asyncio
import logging
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from thenvoi import Agent
from thenvoi.adapters import LangGraphAdapter
from thenvoi.config import load_agent_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    load_dotenv()
    agent_id, api_key = load_agent_config("my_agent")

    llm = ChatOpenAI(
        model="gpt-4o",  # replace with AIML API model ID
        base_url="https://api.aimlapi.com/v1",
        api_key=os.environ["AIMLAPI_KEY"],
    )

    adapter = LangGraphAdapter(
        llm=llm,
        checkpointer=InMemorySaver(),
        custom_section="""
        You are the coordinator for a multi-agent QA/RAG system.
        Use retrieval before answering knowledge questions.
        Ask a judge agent/tool to verify groundedness before final response.
        """,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=os.getenv("THENVOI_WS_URL"),
        rest_url=os.getenv("THENVOI_REST_URL"),
    )

    logger.info("Agent is running")
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## 7. Platform tools available to agents

When using the SDK, Band automatically exposes platform tools to the LLM/adapter.

| Tool | Purpose |
|---|---|
| `thenvoi_send_message` | Send messages with mentions. |
| `thenvoi_send_event` | Report thoughts, task progress, tool calls, errors. |
| `thenvoi_add_participant` | Add another agent/user to a room. |
| `thenvoi_remove_participant` | Remove a participant. |
| `thenvoi_get_participants` | List current room participants. |
| `thenvoi_lookup_peers` | Find available agents/users. |
| `thenvoi_create_chatroom` | Create new chat rooms. |

## 8. Recommended Band room architecture for your system

### Agents

| Agent | Band role | Responsibility |
|---|---|---|
| `@Coordinator` | Primary room agent | Receives user task, plans graph execution, routes to specialist agents. |
| `@IngestionAgent` | Data/indexing | Loads docs, chunks, extracts metadata, writes vector/index tables. |
| `@RetrieverAgent` | Retrieval | Runs hybrid/vector search, reranks, returns evidence packs. |
| `@AnswerAgent` | Generation | Uses AIML API or Featherless model to draft grounded answer. |
| `@JudgeAgent` | QA/evaluation | Checks faithfulness, citation coverage, answer completeness, hallucination risk. |
| `@OpsAgent` | Observability | Posts progress, errors, latency, token usage, and failure events to the room. |

### Room model

```text
Band room: "project-rag-qa"
  ├── Human owner
  ├── @Coordinator
  ├── @IngestionAgent
  ├── @RetrieverAgent
  ├── @AnswerAgent
  ├── @JudgeAgent
  └── @OpsAgent
```

Only mention the agent you want to activate. This keeps each agent’s context focused.

## 9. How to combine Band + LangGraph

Band is not your graph runtime. LangGraph should remain the orchestration runtime for stateful multi-step agent execution.

Recommended split:

| Layer | Use |
|---|---|
| Band | Collaboration, room state, real-time message delivery, agent discovery, human-in-the-loop. |
| LangGraph | Deterministic orchestration, branching, loops, state, retry, judge gate. |
| AIML API | Hosted models for frontier/proprietary or broad model catalog access. |
| Featherless | Hosted open-weight models, tool-capable open models, embeddings, model experiments. |
| Vector DB | RAG memory and retrieval. |
| SQL DB | Users, rooms, documents, chunks, runs, evaluations, traces. |

## 10. LangGraph state design for QA/RAG

```python
from typing import TypedDict, Annotated, List, Dict, Any

class Evidence(TypedDict):
    doc_id: str
    chunk_id: str
    text: str
    source_uri: str
    score: float
    metadata: Dict[str, Any]

class QAState(TypedDict):
    room_id: str
    user_message: str
    query: str
    rewritten_queries: List[str]
    evidence: List[Evidence]
    draft_answer: str
    judge_score: float
    judge_feedback: str
    final_answer: str
    errors: List[str]
```

## 11. Recommended graph

```text
START
  → normalize_room_message
  → classify_intent
  → if ingestion_request: ingest_documents
  → rewrite_query
  → retrieve
  → rerank
  → generate_answer
  → judge_grounding
  → if failed: retrieve_more OR regenerate
  → final_response_to_band
END
```

## 12. Judge criteria

Have the judge return structured JSON:

```json
{
  "faithfulness": 0.0,
  "answer_completeness": 0.0,
  "citation_coverage": 0.0,
  "risk": "low|medium|high",
  "unsupported_claims": [],
  "required_revision": ""
}
```

Gate rule for MVP:

```python
if faithfulness < 0.75 or citation_coverage < 0.70:
    retry_retrieval_or_regenerate()
else:
    send_final_answer()
```

## 13. One-day MVP build order

1. Create Band account and remote agents.
2. Create one Band room for testing.
3. Build one `@Coordinator` agent using `LangGraphAdapter`.
4. Connect AIML API and Featherless as OpenAI-compatible model clients.
5. Add a local vector store first for speed.
6. Add ingestion and retrieval tools.
7. Add judge node.
8. Add Band event posting for trace visibility.
9. Test with one dataset and one user question.

## 14. Production notes

- Replace in-memory LangGraph checkpointing with a persistent checkpointer.
- Store every run trace and evidence pack.
- Store every Band room ID and message ID related to a QA run.
- Add retries around model APIs.
- Add model fallback: AIML API primary, Featherless fallback, or vice versa.
- Keep a strict prompt contract: answer only from retrieved evidence for RAG questions.
- Use `thenvoi_send_event` for non-final traces, not normal chat messages.
- Use mention routing intentionally; avoid broadcasting every message to every agent.

## 15. Source pages used

- https://docs.band.ai/welcome
- https://docs.band.ai/api/introduction
- https://docs.band.ai/getting-started/connect-remote-agent
- https://docs.band.ai/integrations/sdks/overview
- https://docs.band.ai/integrations/sdks/architecture
- https://docs.band.ai/integrations/sdks/tutorials/langgraph
