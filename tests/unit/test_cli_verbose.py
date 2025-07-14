import io
import os
import sys
from contextlib import redirect_stdout

import pytest

# Ensure fake API key so real workflow path is used but FakeListLLM keeps it offline
os.environ.setdefault("OPENAI_API_KEY", "sk-test-verbose")

import essay_agent.cli as cli


@pytest.mark.parametrize("stop_phase", ["outline", "brainstorm"])
def test_cli_verbose_trace(capsys, stop_phase):  # noqa: D401
    """CLI --verbose should print start / end banners up to *stop_phase*."""

    args = [
        "write",
        "-p",
        "Describe a challenge",
        "--verbose",
        "--steps",
        stop_phase,
        "--user",
        "test_user_verbose",
    ]

    buf = io.StringIO()
    with redirect_stdout(buf):
        # Invoke CLI; ensure it doesn't raise SystemExit
        cli.main(args)

    out = buf.getvalue()

    # Always see brainstorm
    assert "▶ brainstorm" in out
    assert "✔ brainstorm" in out

    if stop_phase == "outline":
        assert "▶ outline" in out
        assert "✔ outline" in out
        # Ensure later phases are absent
        assert "draft" not in out
    else:
        # stop at brainstorm – outline banner absent
        assert "outline" not in out 