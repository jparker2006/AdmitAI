import io
import os
from contextlib import redirect_stdout

import essay_agent.cli as cli


def test_streaming_formatter_output():
    """Ensure formatter produces human-readable output and is streamed."""
    if os.getenv("ESSAY_AGENT_OFFLINE_TEST") == "1":
        import pytest
        pytest.skip("Skip CLI streaming test in offline mode")

    os.environ["OPENAI_API_KEY"] = "sk-offline-test"

    args = [
        "write",
        "-p",
        "Describe a challenge you overcame",
        "--show-prompts",
        "--steps",
        "brainstorm",
        "--user",
        "test_streaming",
    ]

    buf = io.StringIO()
    with redirect_stdout(buf):
        cli.main(args)

    out = buf.getvalue()

    # After the RESULT header we expect numbered list formatting (e.g., "1. ")
    assert "RESULT:" in out
    # At least one numbered item present
    assert any(line.strip().startswith("1.") for line in out.splitlines()) 