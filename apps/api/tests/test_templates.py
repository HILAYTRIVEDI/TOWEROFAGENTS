import pytest

from workflows.templates import get_template


def test_hr_template_is_deep_and_requires_policy() -> None:
    template = get_template("hr-candidate-screening")
    assert template.depth == "deep"
    assert "hiring_policy" in template.required_artifacts


def test_unknown_template_fails() -> None:
    with pytest.raises(ValueError):
        get_template("missing")

