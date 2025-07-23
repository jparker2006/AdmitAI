import io
import os
from contextlib import redirect_stdout

import pytest

import essay_agent.cli as cli


def test_prompt_inspector_cli_flag(capsys):
    """CLI flag --show-prompts should print planner prompt and raw plan."""
    # Skip if running in constrained offline mode – heavy CLI path
    if os.getenv("ESSAY_AGENT_OFFLINE_TEST") == "1":
        import pytest
        pytest.skip("Skip CLI inspection in offline stub mode")

    os.environ["OPENAI_API_KEY"] = "sk-offline-test"

    args = [
        "write",
        "-p",
        "Describe a challenge",
        "--show-prompts",
        "--steps",
        "brainstorm",
        "--user",
        "test_prompt_inspector",
    ]

    buf = io.StringIO()
    with redirect_stdout(buf):
        cli.main(args)

    out = buf.getvalue()

    assert "---- PLANNER PROMPT ----" in out
    assert "---- RAW PLAN ----" in out
    # Tool execution banners
    assert "=== TOOL »" in out 