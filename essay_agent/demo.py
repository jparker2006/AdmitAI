from __future__ import annotations

"""essay_agent.demo

A minimal CLI walkthrough of the complete essay workflow *without* any LLM
calls or external dependencies.  Serves as a smoke-test that the codebase can
run end-to-end while later sections are still under construction.

Usage
-----
$ python -m essay_agent.demo            # human-readable output
$ python -m essay_agent.demo --json     # machine-readable JSON output

The entrypoint is also used by integration tests.
"""

import argparse
import json
import sys
import textwrap
from typing import Dict, List

from essay_agent.models import EssayPrompt, UserProfile
from essay_agent.tools import register_tool

# ---------------------------------------------------------------------------
# Mock tool implementations (deterministic / offline) ------------------------
# ---------------------------------------------------------------------------
# These stubs allow Planner/Executor experiments and provide realistic output
# structure for the CLI demo.  Each tool registers itself so that future code
# using TOOL_REGISTRY can still resolve them.
# ---------------------------------------------------------------------------


@register_tool("brainstorm")
def brainstorm(prompt: EssayPrompt, profile: UserProfile) -> List[str]:
    """Return three canned story ideas based on the prompt text."""

    _ = (prompt, profile)  # unused in stub implementation
    return [
        "Overcoming cultural barriers in a new country",
        "Leading a coding club to its first competition win",
        "Confronting stage fright before the big performance",
    ]


@register_tool("outline")
def outline(story: str) -> str:
    """Return a one-paragraph outline for the chosen story."""

    return textwrap.dedent(
        f"""
        Hook: A single moment that changed everything.\n
        Context: I had just arrived in the U.S. and barely spoke the language.\n
        Conflict: Navigating school, friendships, and identity was overwhelming.\n
        Growth: Through debate club and late-night study sessions, I found my voice.\n
        Reflection: This journey taught me resilience and the power of empathy.
        """
    ).strip()


@register_tool("draft")
def draft(outline_text: str) -> str:
    """Expand the outline into a short essay draft."""

    return (
        "When I first moved to the United States, the hallway chatter sounded like \
        a fast-forwarded movie.  Each day was a lesson in translation, not just of \
        words but of culture.  Joining the debate club was a daring leap into this \
        whirlwind, yet it became the arena where my voice transformed from a \
        whisper into conviction."  # noqa: E501
    )


@register_tool("revise")
def revise(draft_text: str) -> str:
    """Return a lightly revised version of the draft."""

    return draft_text + " (revised for clarity)"


@register_tool("polish")
def polish(revised_text: str) -> str:
    """Return a polished final essay string."""

    return revised_text + " (polished for submission)"


# ---------------------------------------------------------------------------
# CLI orchestration ----------------------------------------------------------
# ---------------------------------------------------------------------------

def _validate_non_empty(name: str, value: str) -> None:
    if not value:
        raise RuntimeError(f"{name} returned an empty result.")


def run_demo(*, as_json: bool = False) -> str | Dict[str, str]:
    """Run the mock essay workflow.

    Args:
        as_json: if True, return JSON-serializable dict instead of printing.
    Returns:
        Either the final essay string (human mode) or dict with all phase outputs.
    """

    prompt = EssayPrompt(text="Describe a challenge you overcame.")
    # Minimal user profile for demonstration
    profile = UserProfile.model_validate(
        {
            "user_info": {
                "name": "Demo Student",
                "grade": 12,
                "intended_major": "Computer Science",
                "college_list": ["Generic University"],
                "platforms": [],
            },
            "academic_profile": {
                "gpa": 3.9,
                "test_scores": {"SAT": 1550},
                "courses": [],
                "activities": [],
            },
            "core_values": [],
        }
    )

    outputs: Dict[str, str] = {}

    try:
        # 1. Brainstorm ------------------------------------------------------
        ideas = brainstorm(prompt, profile)
        outputs["brainstorm"] = "\n".join(ideas)
        _validate_non_empty("brainstorm", outputs["brainstorm"])
        print("[Brainstorming] 3 ideas generated…")

        # 2. Outline ---------------------------------------------------------
        outline_text = outline(ideas[0])
        outputs["outline"] = outline_text
        _validate_non_empty("outline", outline_text)
        print("[Outlining] Outline ready…")

        # 3. Draft -----------------------------------------------------------
        draft_text = draft(outline_text)
        outputs["draft"] = draft_text
        _validate_non_empty("draft", draft_text)
        print("[Drafting] Draft complete…")

        # 4. Revise ----------------------------------------------------------
        revised_text = revise(draft_text)
        outputs["revised"] = revised_text
        _validate_non_empty("revised", revised_text)
        print("[Revising] Draft revised…")

        # 5. Polish ----------------------------------------------------------
        final_text = polish(revised_text)
        outputs["final_essay"] = final_text
        _validate_non_empty("final_essay", final_text)
        print("[Polishing] Essay polished!")

    except Exception as exc:  # pragma: no cover
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    # Human-readable output ---------------------------------------------------
    if not as_json:
        separator = "=" * 20 + " FINAL ESSAY " + "=" * 20
        print(separator)
        print(final_text)
        return final_text

    # JSON output ------------------------------------------------------------
    return outputs


def main(argv: List[str] | None = None) -> None:  # noqa: D401
    parser = argparse.ArgumentParser(description="Essay Agent Demo CLI")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of human-readable text.",
    )
    args = parser.parse_args(argv)

    result = run_demo(as_json=args.json)

    if args.json:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main() 