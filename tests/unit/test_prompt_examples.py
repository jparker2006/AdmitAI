import importlib
import inspect
from pathlib import Path

from essay_agent.prompts.example_registry import EXAMPLE_REGISTRY
from essay_agent.tools import REGISTRY
from essay_agent.prompts import brainstorm, outline


def test_registry_covers_all_tools():
    # Refresh registry to pick up any late-registered tools via patched hook
    import essay_agent.tools as _t
    missing = set(_t.REGISTRY) - set(EXAMPLE_REGISTRY)
    assert not missing, f"Missing examples for tools: {missing}"


def test_examples_length():
    long_ones = [k for k, v in EXAMPLE_REGISTRY.items() if len(v) > 250]
    assert not long_ones, f"Example strings exceed 250 chars: {long_ones}"


def test_no_stub_for_key_tools():
    critical = ["draft", "revise", "polish", "fix_grammar", "transition_suggestion"]
    for k in critical:
        assert "stub for" not in EXAMPLE_REGISTRY[k], f"Stub example still present for {k}"


def test_brainstorm_outline_have_example_blocks():
    for mod in (brainstorm, outline):
        prompt_obj = None
        # Each module exposes *something*_PROMPT variable
        for name, value in inspect.getmembers(mod):
            if name.endswith("PROMPT"):
                prompt_obj = value
                break
        assert prompt_obj is not None, f"No PROMPT constant in {mod.__name__}"
        text = prompt_obj.template  # type: ignore[attr-defined]
        assert "<example_output>" in text, f"Missing example block in {mod.__name__}"
        assert len(text.split()) < 650, f"Prompt too long in {mod.__name__}" 