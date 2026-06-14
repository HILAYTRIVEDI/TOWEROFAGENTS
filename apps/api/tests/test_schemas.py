import pytest
from pydantic import ValidationError

from models.schemas import AgentFinding


def test_agent_finding_confidence_is_bounded() -> None:
    with pytest.raises(ValidationError):
        AgentFinding(
            agent_name="Verifier",
            finding_type="risk",
            severity="high",
            title="Unsupported",
            content="No evidence",
            confidence=1.2,
        )

