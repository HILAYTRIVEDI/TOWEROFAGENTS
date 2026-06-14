# AIML API Documentation Notes for LangGraph Multi-Agent QA/RAG

> Source base: https://docs.aimlapi.com/ and https://aimlapi.com/
> Goal: use AIML API as an OpenAI-compatible model provider inside a LangGraph + Band multi-agent QA/RAG system.
> Important limitation: this file summarizes/extracts reachable public docs pages. It is not a byte-for-byte mirror of every page.

## 1. What AIML API is

AIML API is a unified API gateway for many AI models and modalities: chat, reasoning, image, video, audio/voice, search, embeddings, code, vision, and other model classes.

For your system, the most relevant categories are:

- Chat/text LLMs.
- Reasoning models.
- Code models.
- Function/tool-calling capable models.
- Embedding models.
- Vision models if you ingest screenshots/images/PDF pages.
- Web-search capable models if you want online QA.

## 2. OpenAI-compatible base URL

AIML API docs show usage through the OpenAI Python SDK by changing the base URL and API key:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.aimlapi.com/v1",
    api_key="<YOUR_AIMLAPI_KEY>",
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Write a one-sentence story about numbers."}],
)

print(response.choices[0].message.content)
```

In LangChain/LangGraph, configure it as an OpenAI-compatible chat model:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="<aiml-model-id>",
    base_url="https://api.aimlapi.com/v1",
    api_key="<YOUR_AIMLAPI_KEY>",
    temperature=0.2,
)
```

## 3. Main endpoints

### Chat completions

All text/chat models use:

```text
POST https://api.aimlapi.com/v1/chat/completions
```

Use this endpoint for:

- Normal chat.
- Multi-agent reasoning.
- RAG answer generation.
- Judge/evaluator responses.
- Tool/function-calling models.
- Streaming responses.

### Model list

AIML API provides an unauthenticated model list endpoint:

```text
GET https://api.aimlapi.com/models
```

The response contains a list of model objects. Representative fields include:

| Field | Meaning |
|---|---|
| `id` | Unique model ID to pass as `model`. |
| `type` | Model interaction type, such as chat completion. |
| `info` | Metadata for the model. |
| `features` | Supported capabilities/features. |
| `endpoints` | API endpoints the model supports. |

Use this endpoint at app startup or through an admin sync job to populate a local model registry.

## 4. Important capabilities

### Chat completion

A chat model receives role-based messages and returns a structured response. Roles include:

- `system`: high-level behavior and constraints.
- `user`: user request.
- `assistant`: model response.
- `tool`: tool result after a tool/function call.

### Streaming

AIML API supports streaming for text models using the `stream` parameter. Use streaming for UI responsiveness in the Band room or frontend, but store the final full answer in the run trace.

### Function calling

Function calling lets the model output a JSON object describing which external function/tool to call and with what arguments. Your code executes the function and sends the result back to the model.

Important safety note:

- The model does not execute functions by itself.
- The model may hallucinate parameters.
- Add confirmation for real-world actions such as sending email, purchases, posting online, deleting data, or database writes.

In a RAG system, safe function tools include:

- `search_documents(query, filters)`
- `get_chunk(chunk_id)`
- `rerank(query, chunk_ids)`
- `submit_judgement(answer, evidence)`
- `send_band_event(type, payload)`

### Reasoning/thinking models

Use reasoning-capable models for:

- Query decomposition.
- Planning.
- Complex QA.
- Judge/evaluator node.
- Error analysis.

Do not use expensive reasoning models for every step. Use cheaper/fast models for routing, rewriting, and simple extraction.

### Embeddings

AIML API includes embedding model categories. For RAG, use embedding models to convert chunks and queries into vectors.

Recommended ingestion flow:

```text
Document → parser → clean text → chunker → metadata extractor → embedding model → vector DB
```

Recommended query flow:

```text
User query → query rewrite → embedding model → vector search → rerank → answer generation
```

## 5. Model registry table

Create a local model registry so your agents can choose providers and fallbacks dynamically.

```sql
CREATE TABLE model_registry (
  id TEXT PRIMARY KEY,
  provider TEXT NOT NULL, -- 'aimlapi'
  model_type TEXT NOT NULL, -- chat, embedding, vision, image, etc.
  context_window INTEGER,
  supports_streaming BOOLEAN DEFAULT FALSE,
  supports_tools BOOLEAN DEFAULT FALSE,
  supports_reasoning BOOLEAN DEFAULT FALSE,
  supports_vision BOOLEAN DEFAULT FALSE,
  endpoints JSONB,
  features JSONB,
  raw_metadata JSONB,
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

## 6. Recommended AIML API usage inside LangGraph

Use multiple AIML clients/models by task:

| Graph node | Model type | Temperature | Notes |
|---|---|---:|---|
| `intent_router` | fast chat model | 0.0 | Classify request: QA, ingestion, code, admin. |
| `query_rewriter` | cheap chat/reasoning | 0.1 | Generate 2–5 search queries. |
| `answer_generator` | strong chat model | 0.2 | Generate grounded answer from evidence. |
| `judge` | reasoning model | 0.0 | Score answer vs evidence. |
| `fallback_answer` | alternate strong model | 0.2 | Used if primary fails/rate-limits. |

## 7. Example: AIML API client wrapper

```python
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

AIML_BASE_URL = "https://api.aimlapi.com/v1"


def get_aiml_chat(model: str, temperature: float = 0.2):
    return ChatOpenAI(
        model=model,
        base_url=AIML_BASE_URL,
        api_key=os.environ["AIMLAPI_KEY"],
        temperature=temperature,
    )


def get_aiml_embeddings(model: str):
    return OpenAIEmbeddings(
        model=model,
        base_url=AIML_BASE_URL,
        api_key=os.environ["AIMLAPI_KEY"],
    )
```

## 8. Integration with Band + LangGraph

AIML API sits behind the LangGraph nodes, not directly behind Band.

```text
Band room message
  ↓
Band SDK / LangGraphAdapter
  ↓
LangGraph node
  ↓
AIML API model call
  ↓
LangGraph state update
  ↓
Band SDK sends response/event
```

## 9. Error handling and reliability

For production-grade behavior:

- Timebox every model call.
- Add retries with exponential backoff.
- Track token usage and latency per node.
- Add provider fallback to Featherless for open models.
- Cache embeddings by `content_hash + embedding_model`.
- Cache model list locally; refresh daily or manually.
- Record raw model ID and provider for every generated answer.

## 10. Recommended environment variables

```env
AIMLAPI_KEY=...
AIMLAPI_BASE_URL=https://api.aimlapi.com/v1
AIMLAPI_DEFAULT_CHAT_MODEL=...
AIMLAPI_DEFAULT_REASONING_MODEL=...
AIMLAPI_DEFAULT_EMBEDDING_MODEL=...
```

## 11. One-day MVP with AIML API

1. Use AIML API for the main answer model.
2. Use AIML API or local embeddings for vectors.
3. Add only one judge model first.
4. Hardcode 2–3 model IDs in `.env` initially.
5. Add `/models` sync only after the core graph works.

## 12. Source pages used

- https://docs.aimlapi.com/
- https://docs.aimlapi.com/quickstart/simple-model
- https://docs.aimlapi.com/api-references/text-models-llm
- https://docs.aimlapi.com/api-references/service-endpoints/complete-model-list
- https://docs.aimlapi.com/capabilities/completion-or-chat-models
- https://docs.aimlapi.com/capabilities/streaming-mode
- https://docs.aimlapi.com/capabilities/function-calling
- https://docs.aimlapi.com/capabilities/thinking-reasoning
- https://docs.aimlapi.com/api-references/model-database
