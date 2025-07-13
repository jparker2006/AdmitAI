import json
import subprocess
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]


def _run_demo(extra_args=None):
    args = [sys.executable, "-m", "essay_agent.demo"]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(args, capture_output=True, text=True, cwd=PACKAGE_ROOT)


def test_demo_cli_human_output():
    proc = _run_demo()
    assert proc.returncode == 0, proc.stderr
    assert "FINAL ESSAY" in proc.stdout


def test_demo_cli_json_output():
    proc = _run_demo(["--json"])
    assert proc.returncode == 0, proc.stderr
    import re
    match = re.search(r"\{.*\}", proc.stdout, flags=re.DOTALL)
    assert match, "No JSON object found in demo output"
    data = json.loads(match.group(0))
    assert set(data.keys()) == {
        "brainstorm",
        "outline",
        "draft",
        "revised",
        "final_essay",
    }
    assert data["final_essay"].endswith("(polished for submission)") 