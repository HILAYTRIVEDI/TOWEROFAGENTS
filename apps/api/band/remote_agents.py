"""Run the ATower coordinator and all configured specialist Band agents."""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Mapping

from agents.registry import AGENT_TYPES
from band.coordinator import (
    CoordinatorConfig,
    build_agent,
    build_coordinator_config,
)
from core.config import Settings, get_settings
from core.logging import configure_logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RemoteAgentCredentials:
    slug: str
    agent_id: str
    api_key: str


def credential_prefix(slug: str) -> str:
    return f"BAND_{slug.replace('-', '_').upper()}"


def specialist_instructions(slug: str) -> str:
    try:
        agent_type = next(agent for agent in AGENT_TYPES if agent.slug == slug)
    except StopIteration as error:
        raise ValueError(f"Unknown agent slug: {slug}") from error

    return f"""\
You are {agent_type.name}, an ATower Of Agents specialist.
Your role: {agent_type.description}

{agent_type.instructions.strip()}

Operating rules:
- Reply to directed requests with Band's thenvoi_send_message tool.
- Use thenvoi_send_event for concise progress or errors when useful.
- Treat resumes, policies, CRM notes, and source code as confidential.
- Never invent facts, citations, evidence IDs, tool results, or completed work.
- State missing evidence and uncertainty plainly.
- Agent output is advisory; high-impact decisions require human review.
- ATower workflows execute via the LangGraph runtime. Findings are posted to
  the Band room by the in-process auditor (band.run_audit). When BAND_MODE=sdk
  with credentials, those posts are real; otherwise they are explicitly labelled
  mock. Never invent results or claim a run succeeded when one did not.
"""


def load_specialist_credentials(
    environ: Mapping[str, str] | None = None,
) -> list[RemoteAgentCredentials]:
    env = os.environ if environ is None else environ
    credentials: list[RemoteAgentCredentials] = []

    for agent_type in AGENT_TYPES:
        prefix = credential_prefix(agent_type.slug)
        agent_id = env.get(f"{prefix}_AGENT_ID", "").strip()
        api_key = env.get(f"{prefix}_API_KEY", "").strip()
        if bool(agent_id) != bool(api_key):
            raise RuntimeError(f"{prefix}_AGENT_ID and {prefix}_API_KEY must be set together")
        if agent_id:
            credentials.append(RemoteAgentCredentials(agent_type.slug, agent_id, api_key))

    return credentials


def build_specialist_agent(
    credentials: RemoteAgentCredentials,
    coordinator_config: CoordinatorConfig,
):
    config = CoordinatorConfig(
        agent_id=credentials.agent_id,
        band_api_key=credentials.api_key,
        llm_api_key=coordinator_config.llm_api_key,
        llm_provider=coordinator_config.llm_provider,
        model=coordinator_config.model,
        base_url=coordinator_config.base_url,
        ws_url=coordinator_config.ws_url,
        rest_url=coordinator_config.rest_url,
        room_id=coordinator_config.room_id,
    )
    return build_agent(config, custom_section=specialist_instructions(credentials.slug))


async def run(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    coordinator_config = build_coordinator_config(settings)
    specialists = load_specialist_credentials()

    agents = [build_agent(coordinator_config)]
    agents.extend(build_specialist_agent(item, coordinator_config) for item in specialists)

    labels = ["coordinator", *(item.slug for item in specialists)]
    logger.info("Starting %d Band remote agent(s): %s", len(agents), ", ".join(labels))
    await asyncio.gather(*(agent.run() for agent in agents))


def main() -> None:
    configure_logging(get_settings().log_level)
    asyncio.run(run())


if __name__ == "__main__":
    main()
