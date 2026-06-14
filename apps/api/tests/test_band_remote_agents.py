import pytest

from agents.registry import AGENT_TYPES
from band.remote_agents import (
    credential_prefix,
    load_specialist_credentials,
    specialist_instructions,
)


def test_all_registered_agents_have_safe_band_instructions() -> None:
    for agent_type in AGENT_TYPES:
        instructions = specialist_instructions(agent_type.slug)
        assert agent_type.name in instructions
        assert "thenvoi_send_message" in instructions
        assert "Never claim a workflow ran" in instructions


def test_loads_all_complete_specialist_credentials() -> None:
    env: dict[str, str] = {}
    for index, agent_type in enumerate(AGENT_TYPES):
        prefix = credential_prefix(agent_type.slug)
        env[f"{prefix}_AGENT_ID"] = f"agent-{index}"
        env[f"{prefix}_API_KEY"] = f"key-{index}"

    credentials = load_specialist_credentials(env)

    assert [item.slug for item in credentials] == [agent.slug for agent in AGENT_TYPES]


def test_skips_unregistered_agents() -> None:
    credentials = load_specialist_credentials(
        {
            "BAND_BIAS_REVIEWER_AGENT_ID": "bias-id",
            "BAND_BIAS_REVIEWER_API_KEY": "bias-key",
        }
    )

    assert [item.slug for item in credentials] == ["bias-reviewer"]


def test_empty_environment_has_no_specialists() -> None:
    assert load_specialist_credentials({}) == []


def test_rejects_partial_credentials() -> None:
    with pytest.raises(RuntimeError, match="must be set together"):
        load_specialist_credentials({"BAND_POLICY_GUARDIAN_AGENT_ID": "guardian-id"})


def test_credential_prefix_is_shell_safe() -> None:
    assert credential_prefix("resume-jd-matcher") == "BAND_RESUME_JD_MATCHER"
