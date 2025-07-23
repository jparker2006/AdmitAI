import os
import random
import importlib

import pytest

os.environ["ESSAY_AGENT_OFFLINE_TEST"] = "1"  # ensure offline stubs

from essay_agent.tools import REGISTRY, TOOL_ARG_SPEC
from essay_agent.utils.arg_resolver import ArgResolver, MissingRequiredArgError
from essay_agent.utils.test_helpers import universal_context

resolver = ArgResolver()
ctx = universal_context()

# Allow skipping a small set of tools that legitimately require external resources or unusual args
SKIP_TOOLS = set()


def test_resolver_completeness():
    missing = []
    for name in REGISTRY:
        if name in SKIP_TOOLS:
            continue
        required = TOOL_ARG_SPEC[name]["required"]
        try:
            resolver.resolve(name, planner_args={}, context=ctx, user_input="test", verbose=False)
        except MissingRequiredArgError:
            # Only complain if tool declares required args
            if required:
                missing.append(name)
    assert not missing, f"Resolver failed for: {', '.join(missing)}" 