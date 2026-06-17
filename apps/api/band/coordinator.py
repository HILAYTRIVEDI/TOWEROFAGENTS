"""Live Band coordinator agent entrypoint.

This is a long-lived process, separate from the FastAPI app. The API never
holds a Band WebSocket connection, so without this process the `@ATower
Coordinator` remote agent stays silent even though it is a room participant.

The coordinator joins Band via the official SDK (`thenvoi`), drives a LangGraph
adapter backed by a Featherless OpenAI-compatible model, and replies to mentions
using Band platform tools. It does NOT execute HR screening or any product
workflow: `/workflows/{id}/run` is still 501. The agent is instructed to say so
plainly and point users at artifact upload instead of fabricating results.

Run it with `python -m band.coordinator` (the `band-agent` compose service does
this automatically). Requires `BAND_MODE=sdk` plus Band and a tool-capable
OpenAI-compatible model provider.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from core.config import Settings, get_settings
from core.logging import configure_logging

logger = logging.getLogger(__name__)

# Band's public defaults (docs: THENVOI_REST_URL / THENVOI_WS_URL).
DEFAULT_THENVOI_REST_URL = "https://app.band.ai/"
DEFAULT_THENVOI_WS_URL = "wss://app.band.ai/api/v1/socket/websocket"
DEFAULT_AIML_BASE_URL = "https://api.aimlapi.com/v1"

# ATower-specific behavior. Kept honest about current capabilities: the
# coordinator can talk and coordinate in the room, but cannot run the HR
# screening workflow yet, so it must never claim a screening was performed.
COORDINATOR_INSTRUCTIONS = """\
You are the ATower Coordinator, the primary agent in an ATower Of Agents Band room.
ATower is a control tower for enterprise AI-agent workflows (HR Candidate Screening
is the flagship workflow).

You can:
- Greet and coordinate with people in the room.
- Explain what ATower does and what artifacts a workflow needs.
- Acknowledge mentions and answer questions about the platform.

You CANNOT yet:
- Run HR candidate screening or any product workflow. Workflow execution is not
  implemented (the API returns 501 Not Implemented).
- Retrieve resumes, job descriptions, or policies, or produce a decision packet.

Rules:
- Never claim a screening, evaluation, retrieval, or decision was performed. If
  asked to screen a candidate or run a workflow, say clearly that execution is not
  implemented yet, and direct the user to create the workflow and upload the
  required artifacts (resume, job description, hiring policy) in the ATower app.
- Never invent candidate scores, evidence IDs, citations, or outcomes.
- Be concise and honest. When you are unsure or lack a capability, say so.
"""


@dataclass(frozen=True)
class CoordinatorConfig:
    """Validated, secret-bearing configuration for the live coordinator."""

    agent_id: str
    band_api_key: str
    llm_api_key: str
    llm_provider: str
    model: str
    base_url: str
    ws_url: str
    rest_url: str
    room_id: str | None


def build_coordinator_config(settings: Settings) -> CoordinatorConfig:
    """Validate live config and resolve endpoints/model.

    Raises RuntimeError with an explicit, actionable message when the
    coordinator is not configured to run live. No network or SDK access.
    """

    if settings.band_mode != "sdk":
        raise RuntimeError(
            "Band coordinator requires BAND_MODE=sdk "
            f"(current BAND_MODE={settings.band_mode!r}). Set BAND_MODE=sdk to run live."
        )

    band_missing = [
        name
        for name, value in (
            ("BAND_AGENT_ID", settings.band_agent_id),
            ("BAND_API_KEY", settings.band_api_key),
        )
        if not value
    ]
    if band_missing:
        raise RuntimeError(
            "Band coordinator is missing required configuration: " + ", ".join(band_missing)
        )

    provider = settings.llm_provider.lower()
    if provider == "aiml":
        llm_api_key = settings.aiml_api_key
        model = settings.aiml_default_model
        base_url = DEFAULT_AIML_BASE_URL
        missing = [
            name
            for name, value in (
                ("AIML_API_KEY", llm_api_key),
                ("AIML_DEFAULT_MODEL", model),
            )
            if not value
        ]
    elif provider in {"featherless", "auto"}:
        provider = "featherless"
        llm_api_key = settings.featherless_api_key
        model = settings.featherless_tool_model or settings.featherless_default_model
        base_url = settings.featherless_base_url
        missing = [
            name
            for name, value in (
                ("FEATHERLESS_API_KEY", llm_api_key),
                ("FEATHERLESS_TOOL_MODEL or FEATHERLESS_DEFAULT_MODEL", model),
            )
            if not value
        ]
    else:
        raise RuntimeError(
            "Band coordinator requires LLM_PROVIDER=aiml or LLM_PROVIDER=featherless "
            f"when BAND_MODE=sdk (current LLM_PROVIDER={settings.llm_provider!r})."
        )

    if missing:
        raise RuntimeError(
            "Band coordinator is missing required model configuration: " + ", ".join(missing)
        )

    # Narrowed to str by the checks above; assert for the type checker.
    assert settings.band_agent_id and settings.band_api_key and llm_api_key and model

    return CoordinatorConfig(
        agent_id=settings.band_agent_id,
        band_api_key=settings.band_api_key,
        llm_api_key=llm_api_key,
        llm_provider=provider,
        model=model,
        base_url=base_url,
        ws_url=settings.thenvoi_ws_url or DEFAULT_THENVOI_WS_URL,
        rest_url=settings.thenvoi_rest_url or DEFAULT_THENVOI_REST_URL,
        room_id=settings.band_default_room_id,
    )


def build_agent(
    config: CoordinatorConfig,
    *,
    custom_section: str = COORDINATOR_INSTRUCTIONS,
    chat_openai=None,
    langgraph_adapter=None,
    in_memory_saver=None,
    agent=None,
):
    """Construct the Band SDK agent from validated config.

    SDK/LLM imports are lazy so tests can inject fakes without installing
    `band-sdk` or `langchain-openai`. Returns the result of `Agent.create(...)`.
    """

    if chat_openai is None or langgraph_adapter is None or in_memory_saver is None or agent is None:
        from langchain_openai import ChatOpenAI
        from langgraph.checkpoint.memory import InMemorySaver
        from thenvoi import Agent
        from thenvoi.adapters import LangGraphAdapter

        chat_openai = chat_openai or ChatOpenAI
        langgraph_adapter = langgraph_adapter or LangGraphAdapter
        in_memory_saver = in_memory_saver or InMemorySaver
        agent = agent or Agent

    llm = chat_openai(
        model=config.model,
        base_url=config.base_url,
        api_key=config.llm_api_key,
    )
    adapter = langgraph_adapter(
        llm=llm,
        checkpointer=in_memory_saver(),
        custom_section=custom_section,
    )
    return agent.create(
        adapter=adapter,
        agent_id=config.agent_id,
        api_key=config.band_api_key,
        ws_url=config.ws_url,
        rest_url=config.rest_url,
    )


async def run(settings: Settings | None = None) -> None:
    """Build and run the coordinator until cancelled."""

    settings = settings or get_settings()
    config = build_coordinator_config(settings)
    agent = build_agent(config)
    logger.info(
        "ATower Coordinator starting (agent_id=%s, provider=%s, model=%s, room=%s)",
        config.agent_id,
        config.llm_provider,
        config.model,
        config.room_id or "<none configured>",
    )
    await agent.run()


def main() -> None:
    configure_logging(get_settings().log_level)
    asyncio.run(run())


if __name__ == "__main__":
    main()
