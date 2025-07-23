import subprocess, sys


def test_cli_help_includes_init_and_resume():
    result = subprocess.run(
        [sys.executable, "-m", "essay_agent.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    help_text = result.stdout
    # Ensure both commands appear in the global help
    assert "init" in help_text
    assert "resume" in help_text
    # Short description for resume command (EF-99)
    assert "Resume unfinished essay workflow" in help_text 