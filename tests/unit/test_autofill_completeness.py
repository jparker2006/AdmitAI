"""
Unit test for U4-02 / P5-01: Autofill Argument Completeness

Ensures that for every tool in the TOOL_REGISTRY, the `autofill_args`
function can successfully supply all of its required arguments.
"""

import inspect
import pytest
from unittest.mock import MagicMock

from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.utils.default_args import autofill_args

# Tools that are okay to exclude from this test.
# (e.g., they are wrappers or don't have standard signatures)
EXCLUDED_TOOLS = {
    "echo", # simple wrapper
    "chat_response", # simple wrapper
}

@pytest.mark.parametrize("tool_name, tool_instance", TOOL_REGISTRY.items())
def test_autofill_provides_all_required_args(tool_name, tool_instance):
    """
    For each tool, inspect its signature and assert that autofill_args
    can provide all required parameters.
    """
    if tool_name in EXCLUDED_TOOLS:
        pytest.skip(f"Tool '{tool_name}' is explicitly excluded from autofill test.")

    # The actual callable is often on a 'run' method or the instance itself
    if hasattr(tool_instance, "run") and callable(tool_instance.run):
        func = tool_instance.run
    elif callable(tool_instance):
        func = tool_instance
    else:
        pytest.fail(f"Could not find a callable function for tool '{tool_name}'")

    sig = inspect.signature(func)
    required_args = {
        p.name
        for p in sig.parameters.values()
        if p.default == inspect.Parameter.empty and p.name not in ('self', 'kwargs', 'args')
    }
    
    # If there are no required args, the test passes by default for this tool.
    if not required_args:
        return

    # Simulate a plan step with empty args
    mock_step = {"tool": tool_name, "args": {}}
    
    # Create mock context and memory
    mock_context = {
        "user_profile": {"name": "Test User"},
        "essay_state": {"word_count": 100},
        "recent_chat": [{"role": "user", "content": "help me brainstorm"}],
        "brainstorm_specific": {"best_idea": "a story about a challenge"},
        "outline": {"hook": "...", "context": "...", "conflict": "...", "growth": "...", "conclusion": "..."}
    }
    mock_memory = MagicMock()
    mock_memory.get.side_effect = lambda key, default="": {
        "essay_prompt": "Tell me about a time you faced a challenge.",
        "college": "Stanford University",
    }.get(key, default)
    
    # Run the autofill function
    filled_args = autofill_args(
        step=mock_step,
        context=mock_context,
        memory=mock_memory,
        user_input="Help me brainstorm some ideas for this."
    )
    
    missing_args = required_args - set(filled_args.keys())
    
    assert not missing_args, (
        f"Tool '{tool_name}' is missing required arguments after autofill: {missing_args}. "
        f"Please add a rule to essay_agent/utils/default_args.py."
    ) 