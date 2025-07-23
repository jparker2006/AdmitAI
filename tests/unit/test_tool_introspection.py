import pytest

from essay_agent.tools import REGISTRY, TOOL_ARG_SPEC


def test_catalog_includes_all_tools():
    assert set(TOOL_ARG_SPEC.keys()) == set(REGISTRY.keys()), "Arg spec missing tools"


def test_spec_structure():
    for name, spec in TOOL_ARG_SPEC.items():
        assert "required" in spec and "optional" in spec, f"Spec keys missing for {name}"
        assert isinstance(spec["required"], list) and isinstance(spec["optional"], list)


def test_coverage_ratio():
    # At least 90% of tools should expose some arg info (required or optional)
    total = len(TOOL_ARG_SPEC)
    informative = sum(1 for spec in TOOL_ARG_SPEC.values() if spec["required"] or spec["optional"])
    assert informative / max(total, 1) >= 0.95, "Insufficient arg info coverage" 