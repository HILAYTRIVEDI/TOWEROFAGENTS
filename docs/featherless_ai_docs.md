# Featherless.ai Documentation Notes for LangGraph Multi-Agent QA/RAG

> Source base: https://featherless.ai/docs/
> Goal: use Featherless as an OpenAI-compatible provider for open-weight chat, tool-calling, vision, embeddings, and model experimentation in a LangGraph + Band QA/RAG system.
> Important limitation: this file summarizes/extracts reachable public docs pages. It is not a byte-for-byte mirror of every page.

## 1. What Featherless is

Featherless is a serverless AI inference platform focused on open-weight models. It provides API access to open models such as Qwen, Llama, Mistral, DeepSeek, RWKV, and other model families without requiring you to manage inference infrastructure.

For your architecture, Featherless is useful for:

- Open-weight chat models.
- Tool/function calling with supported models.
- Embeddings.
- Vision-capable models.
- Model fallback and experimentation.
- Avoiding local GPU infrastructure for hackathon/MVP use.

## 2. OpenAI-compatible base URL

Featherless is OpenAI-compatible for common text generation workflows. Use the OpenAI SDK with a changed base URL and API key:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key="FEATHERLESS_API_KEY",
)

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
)

print(response.choices[0].message.content)
```

LangChain/LangGraph wrapper:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="Qwen/Qwen2.5-7B-Instruct",
    base_url="https://api.featherless.ai/v1",
    api_key="<FEATHERLESS_API_KEY>",
    temperature=0.2,
)
```

## 3. Authentication

Most endpoints require a bearer token:

```http
Authorization: Bearer FEATHERLESS_API_KEY
```

The docs also recommend adding client attribution headers for application integrations:

```http
HTTP-Referer: https://your-app.example
X-Title: Your App Name
```

## 4. Main endpoints

### Chat completions

```text
POST https://api.featherless.ai/v1/chat/completions
```

Use this endpoint for role-based chat and assistant-style interactions.

Representative request body:

```json
{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 100
}
```

### Text completions

```text
POST https://api.featherless.ai/v1/completions
```

Use this when you want prompt-string based completions instead of role-based chat.

### Models

```text
GET https://api.featherless.ai/v1/models
```

The model endpoint lists all catalog models and current state. It can be called with or without authentication.

Representative response item:

```json
{
  "id": "vicgalle/Roleplay-Llama-3-8B",
  "name": "vicgalle/Roleplay-Llama-3-8B",
  "model_class": "llama3-8b-8k",
  "context_length": 8192,
  "max_completion_tokens": 4096
}
```

Use the `id` as the `model` value for chat/completions.

### Embeddings

```text
POST https://api.featherless.ai/v1/embeddings
```

Featherless supports OpenAI-compatible embedding requests for embedding-capable models.

Example:

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-featherless-api-key",
    base_url="https://api.featherless.ai/v1",
)

response = client.embeddings.create(
    model="Qwen/Qwen3-Embedding-8B",
    input="Featherless makes serverless inference simple.",
)

print(response.data[0].embedding[:5])
print(response.usage)
```

Batch example:

```python
response = client.embeddings.create(
    model="Qwen/Qwen3-Embedding-8B",
    input=[
        "The cat sat on the mat.",
        "A kitten is resting on a rug.",
        "Server racks need better airflow.",
    ],
)
```

### Tokenize

Featherless includes `/v1/tokenize` for tokenization-related workflows. Use it to estimate prompt sizes and prevent context overflow.

### Concurrency stream

Featherless includes `/account/concurrency/stream` documentation. Use account-level concurrency data for backpressure and dynamic model routing when scaling.

## 5. Model discovery and filtering

The `/v1/models` endpoint supports optional filters.

Common parameters:

| Parameter | Purpose |
|---|---|
| `q` | Search by model name or ID. |
| `available_on_current_plan` | Filter to models available on the authenticated plan. |
| `page` | Pagination page. |
| `per_page` | Results per page, max 1000. |

Model metadata filters include:

- `license`
- `family`
- `model_class`
- `status`
- `languages`
- `tasks`
- `architectures`
- `training`
- `capabilities`
- `modalities`
- `domains`
- `creative`
- `content_flags`
- `parameter_bucket`
- `popularity_level`

Boolean filters:

- `gated=true|false`
- `conversational=true|false`

Range filters:

- `context_length_min`
- `context_length_max`

Useful model lookup examples:

```bash
# List models available on your plan
curl "https://api.featherless.ai/v1/models?available_on_current_plan=true" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $FEATHERLESS_API_KEY"

# Find tool-capable chat models with at least 32k context
curl -H "Authorization: Bearer $FEATHERLESS_API_KEY" \
  "https://api.featherless.ai/v1/models?capabilities=chat,tool-use&context_length_min=32768"

# Search for Llama models
curl -H "Authorization: Bearer $FEATHERLESS_API_KEY" \
  "https://api.featherless.ai/v1/models?q=llama"
```

## 6. Chat/completion parameters

Featherless supports common generation parameters:

| Parameter | Meaning |
|---|---|
| `model` | Model ID to use. |
| `messages` | Conversation messages for chat completions. |
| `presence_penalty` | Encourages/discourages new tokens based on presence. |
| `frequency_penalty` | Encourages/discourages new tokens based on frequency. |
| `repetition_penalty` | Penalizes repeated tokens from prompt/generated text. |
| `temperature` | Sampling randomness. Lower = deterministic. |
| `top_p` | Nucleus sampling cumulative probability. |
| `top_k` | Number of top tokens to consider. |
| `min_p` | Minimum token probability relative to most likely token. |
| `seed` | Random seed; not guaranteed reliable across multiple servers. |
| `stop` | Stop strings. |
| `stop_token_ids` | Stop token IDs. |
| `include_stop_str_in_output` | Include/exclude stop strings in output. |
| `max_tokens` | Maximum generated tokens. |
| `min_tokens` | Minimum generated tokens before EOS/stop. |

## 7. Tool/function calling

Featherless supports OpenAI-compatible function calling across supported models. Native support is documented for model families including:

- `moonshotai/Kimi-K2-Instruct`
- Qwen 3 family

Function calling flow:

1. Send user message plus `tools` schema to `/v1/chat/completions`.
2. Model returns one or more tool call decisions with arguments.
3. Your app executes the tool.
4. Send tool result back as a `tool` message.
5. Model produces final answer.

Example tool schema shape:

```json
{
  "type": "function",
  "function": {
    "name": "get_current_weather",
    "description": "Get the current weather in a given location",
    "parameters": {
      "type": "object",
      "properties": {
        "location": {"type": "string"}
      },
      "required": ["location"]
    }
  }
}
```

For your RAG app, tool calling should be used for controlled internal tools, not arbitrary external actions.

## 8. Vision

Featherless supports image input through OpenAI-compatible chat completions for vision-capable models. Image input can be sent as URLs or base64-encoded data.

Use vision for:

- Screenshot QA.
- Diagram understanding.
- Image-heavy documents.
- PDF page screenshots when text extraction fails.

## 9. Embeddings for RAG

Recommended use:

- Use Featherless embeddings if you want open-model embeddings without local inference.
- Store `embedding_model`, `embedding_dimensions`, and `content_hash` with every vector.
- Batch inputs to reduce overhead.
- Use `/v1/models?modalities=embedding` or the model catalog to find embedding-capable models.

## 10. Featherless provider wrapper

```python
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

FEATHERLESS_BASE_URL = "https://api.featherless.ai/v1"


def get_featherless_chat(model: str, temperature: float = 0.2):
    return ChatOpenAI(
        model=model,
        base_url=FEATHERLESS_BASE_URL,
        api_key=os.environ["FEATHERLESS_API_KEY"],
        temperature=temperature,
    )


def get_featherless_embeddings(model: str):
    return OpenAIEmbeddings(
        model=model,
        base_url=FEATHERLESS_BASE_URL,
        api_key=os.environ["FEATHERLESS_API_KEY"],
    )
```

## 11. Recommended use in your LangGraph system

| Node | Recommended Featherless use |
|---|---|
| `query_rewriter` | Use a fast Qwen/Llama model. |
| `retrieval_embeddings` | Use `Qwen/Qwen3-Embedding-*` or another embedding-capable model. |
| `tool_agent` | Use Qwen 3 or Kimi-K2 if tool calling is needed. |
| `judge` | Use a stronger reasoning/coding model if available on your plan. |
| `fallback_answer` | Use an open model when AIML API primary fails. |

## 12. Production notes

- Use `/v1/models` to validate context length before selecting a model.
- Check `available_on_current_plan` to avoid 403 errors.
- Handle gated Hugging Face models. A gated model can require the user to ungate it in their connected Hugging Face account.
- Use `context_length` and `max_completion_tokens` to cap prompt sizes.
- Add retry/fallback on 429, 5xx, and timeout.
- Keep per-provider latency and error metrics.
- Use small/cheap models for routing and large models for final synthesis/judging.

## 13. Recommended environment variables

```env
FEATHERLESS_API_KEY=...
FEATHERLESS_BASE_URL=https://api.featherless.ai/v1
FEATHERLESS_DEFAULT_CHAT_MODEL=Qwen/Qwen2.5-7B-Instruct
FEATHERLESS_TOOL_MODEL=Qwen/Qwen3-32B
FEATHERLESS_EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
```

## 14. Source pages used

- https://featherless.ai/docs/overview
- https://featherless.ai/docs/quickstart-guide
- https://featherless.ai/docs/api-overview-and-common-options
- https://featherless.ai/docs/api-reference-models
- https://featherless.ai/docs/completions
- https://featherless.ai/docs/v1-tokenize
- https://featherless.ai/docs/api-reference-error-codes
- https://featherless.ai/docs/tool-calling
- https://featherless.ai/docs/vision
- https://featherless.ai/docs/embeddings
