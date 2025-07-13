from __future__ import annotations

import dotenv
dotenv.load_dotenv()

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


def brainstorm(prompt: EssayPrompt, profile: UserProfile) -> List[str]:
    """Return three canned story ideas based on the prompt text."""

    _ = (prompt, profile)  # unused in stub implementation
    return [
        "Overcoming cultural barriers in a new country",
        "Leading a coding club to its first competition win",
        "Confronting stage fright before the big performance",
    ]


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


def draft(outline_text: str) -> str:
    """Expand the outline into a short essay draft."""

    return (
        "When I first moved to the United States, the hallway chatter sounded like \
        a fast-forwarded movie.  Each day was a lesson in translation, not just of \
        words but of culture.  Joining the debate club was a daring leap into this \
        whirlwind, yet it became the arena where my voice transformed from a \
        whisper into conviction."  # noqa: E501
    )


def revise(draft_text: str) -> str:
    """Return a lightly revised version of the draft."""

    return draft_text + " (revised for clarity)"


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
    try:
        profile = UserProfile.model_validate(
            {
                "user_info": {
                    "name": "Jake Parker",
                    "grade": 12,
                    "intended_major": "Computer Science",
                    "college_list": ["Stanford"],
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
    except Exception:  # pragma: no cover – fallback minimal profile
        profile = UserProfile.model_validate(
            {
                "user_info": {
                    "name": "Demo User",
                    "grade": 12,
                    "intended_major": "Undeclared",
                    "college_list": [],
                    "platforms": [],
                },
                "academic_profile": {
                    "gpa": None,
                    "test_scores": {},
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
    parser.add_argument("prompt", nargs="*", help="Essay prompt to answer. If omitted, uses a default.")
    parser.add_argument("--json", action="store_true", help="Output results as JSON instead of human-readable text.")
    parser.add_argument("--agent", action="store_true", help="Run full EssayAgent workflow (requires OPENAI_API_KEY and implemented tools).")
    args = parser.parse_args(argv)

    if args.agent:
        from essay_agent.agent import EssayAgent
        from essay_agent.models import EssayPrompt
        from essay_agent.tools import REGISTRY as TOOL_REGISTRY

        user_prompt = " ".join(args.prompt).strip() or "Describe a challenge you overcame."
        essay_prompt = EssayPrompt(text=user_prompt, word_limit=650)

        # Remove stub tools registered in this module -----------------------
        for key in ["brainstorm", "outline", "draft", "revise", "polish"]:
            tool = TOOL_REGISTRY.get(key)
            if tool is not None and tool.__module__ == __name__:
                TOOL_REGISTRY.pop(key, None)

        # Re-import real tool modules to ensure registry populated ---------
        import importlib
        for mod_name in [
            "essay_agent.tools.brainstorm",
            "essay_agent.tools.outline",
            "essay_agent.tools.draft",
            "essay_agent.tools.revision",
            "essay_agent.tools.polish",
        ]:
            importlib.import_module(mod_name)

        agent = EssayAgent(user_id="cli_user")
        result_dict = agent.generate_essay(essay_prompt)

        if args.json:
            print(json.dumps(result_dict, indent=2))
        else:
            # Define the order of steps to print
            steps_order = ["brainstorm", "outline", "draft", "revision", "polish"]
            
            print("\n=============================================")
            print("=             AGENT WORKFLOW              =")
            print("=============================================")

            for step_name in steps_order:
                if step_name in result_dict:
                    print(f"\n✅ === STEP: {step_name.upper()} ===\n")
                    step_output = result_dict[step_name]
                    
                    # Custom format for brainstorm stories
                    if step_name == "brainstorm" and isinstance(step_output, dict) and "stories" in step_output:
                        for i, story in enumerate(step_output.get("stories", [])):
                            story_data = story if isinstance(story, dict) else story.dict()
                            print(f"  IDEA {i+1}: {story_data.get('title')}")
                            print(f"    Description: {story_data.get('description')}")
                            print(f"    Prompt Fit: {story_data.get('prompt_fit')}")
                            print(f"    Insights: {', '.join(story_data.get('insights', []))}\n")
                    # Custom format for revision
                    elif step_name == "revision" and isinstance(step_output, dict):
                         print("Revised Draft Snippet:")
                         print(textwrap.indent(step_output.get('revised_draft', '')[:200] + "...", "  "))
                         print("\n  Changes Made:")
                         for change in step_output.get('changes', []):
                             print(f"  - {change}")
                    # General formatted print for others
                    elif isinstance(step_output, (dict, list)):
                         print(json.dumps(step_output, indent=2))
                    else:
                        print(textwrap.indent(str(step_output), "  "))
            
            print("\n\n=============================================")
            print("=              FINAL ESSAY                =")
            print("=============================================")
            print(result_dict.get("final_draft", "Essay not found."))
        return

    # Fallback to stub demo --------------------------------------------------
    # Register stub tools for demo mode
    register_tool("brainstorm")(brainstorm)
    register_tool("outline")(outline)
    register_tool("draft")(draft)
    register_tool("revise")(revise)
    register_tool("polish")(polish)
    
    result = run_demo(as_json=args.json)

    if args.json:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main() 