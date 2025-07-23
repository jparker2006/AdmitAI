import os
import io
from contextlib import redirect_stdout

import pytest

from essay_agent.tools.integration import format_tool_result


def test_brainstorm_formatting():
    result = {"ok": ["Idea one", "Idea two", "Idea three"], "error": None}
    formatted = format_tool_result("brainstorm", result)
    # Expect numbered list starting with 1.
    assert formatted.split("\n")[0].startswith("1. ")
    assert "2. Idea two" in formatted


def test_outline_formatting():
    outline_lines = ["Hook: ...", "Context: ...", "Conflict: ..."]
    result = {"ok": outline_lines, "error": None}
    formatted = format_tool_result("outline", result)
    # Check bullet formatting
    assert formatted.startswith("- ")
    assert formatted.count("- ") == len(outline_lines)


def test_validator_formatting():
    checks = [
        {"name": "word_count", "status": "pass", "message": "within limit"},
        {"name": "grammar", "status": "fail", "message": "typo found"},
    ]
    result = {"ok": {"checks": checks}, "error": None}
    formatted = format_tool_result("structure_validator", result)
    # Should contain both check marks and warnings
    assert "✅" in formatted and "⚠️" in formatted 