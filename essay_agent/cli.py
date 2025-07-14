import argparse
import dotenv
dotenv.load_dotenv()
import json
import os
import sys
from dataclasses import asdict
from typing import Any, Dict, Optional

from essay_agent.agent import EssayAgent
from essay_agent.models import EssayPrompt
from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.memory.user_profile_schema import UserProfile
from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.utils.logging import debug_print

try:
    # tqdm is already a declared dependency in requirements.txt
    from tqdm import tqdm
except ModuleNotFoundError:  # pragma: no cover – fallback minimal progress
    class _TQDMStub:  # type: ignore
        def __init__(self, total: int, disable: bool = False):
            self.disable = disable
            self.total = total
            self.n = 0
        def update(self, n=1):
            self.n += n
        def close(self):
            pass
    tqdm = _TQDMStub  # type: ignore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_profile(user_id: str, profile_path: Optional[str] = None) -> UserProfile:
    """Load **UserProfile** from *profile_path* or SimpleMemory fallback."""

    if profile_path:
        try:
            with open(profile_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            return UserProfile.model_validate(data)  # type: ignore[arg-type]
        except Exception as exc:  # pragma: no cover
            print(f"[ERROR] Failed to load profile JSON – {exc}", file=sys.stderr)
            sys.exit(1)

    # Otherwise pull persisted (or default) profile
    return SimpleMemory.load(user_id)


def _print_human(result: Dict[str, Any]) -> None:
    """Print results in human-readable format."""
    steps_order = ["stories", "outline", "versions", "final_draft", "errors", "debug_log", "stats"]
    
    for key in steps_order:
        if key not in result or not result[key]:
            continue
        header = key.replace("_", " ").title()
        print("\n" + "=" * 10 + f" {header} " + "=" * 10)
        value = result[key]
        if isinstance(value, (dict, list)):
            try:
                print(json.dumps(value, indent=2, default=str))
            except TypeError:
                # Fallback for objects that can't be serialized
                print(str(value))
        else:
            print(value)

    # Print any additional keys not in default order ---------------------
    for key, value in result.items():
        if key in steps_order or not value:
            continue
        header = key.replace("_", " ").title()
        print("\n" + "=" * 10 + f" {header} " + "=" * 10)
        if isinstance(value, (dict, list)):
            try:
                print(json.dumps(value, indent=2, default=str))
            except TypeError:
                # Fallback for objects that can't be serialized
                print(str(value))
        else:
            print(value)


# ---------------------------------------------------------------------------
# Command Implementations
# ---------------------------------------------------------------------------

def _cmd_write(args: argparse.Namespace) -> None:  # noqa: D401
    user_id = args.user
    prompt_text = args.prompt or " ".join(args.prompt_positional or []).strip()
    if not prompt_text:
        prompt_text = input("Essay prompt: ").strip()
    if not prompt_text:
        print("[ERROR] Prompt text must not be empty", file=sys.stderr)
        sys.exit(1)

    word_limit = args.word_limit or 650
    profile = _load_profile(user_id, args.profile)

    # ------------------------------------------------------------------
    # Decide whether to run real agent or demo fallback
    # ------------------------------------------------------------------
    use_demo = not bool(os.getenv("OPENAI_API_KEY"))
    if use_demo and not args.allow_demo:
        print(
            "[ERROR] OPENAI_API_KEY not set. Use --allow-demo to run offline demo.",
            file=sys.stderr,
        )
        sys.exit(2)

    if use_demo:
        from essay_agent.demo import run_demo  # local import to avoid cycles

        debug_print(args.debug, "Running offline demo workflow (stub tools)…")
        outputs = run_demo(as_json=True)
        if args.json:
            print(json.dumps(outputs, indent=2))
        else:
            _print_human(outputs)
        sys.exit(0)

    # ------------------------------------------------------------------
    # Real EssayAgent execution
    # ------------------------------------------------------------------
    essay_prompt = EssayPrompt(text=prompt_text, word_limit=word_limit)
    agent = EssayAgent(user_id=user_id)

    # Persist latest profile so subsequent tool calls can reference
    SimpleMemory.save(user_id, profile)

    # Display progress bar -------------------------------------------------
    phases = ["brainstorm", "outline", "draft", "revision", "polish"]
    bar = tqdm(total=len(phases), disable=args.json)

    result = agent.run(essay_prompt, profile, debug=args.debug)

    # Close progress bar – update to full if still open
    bar.update(len(phases) - bar.n)
    bar.close()

    result_dict = asdict(result)

    if args.json:
        print(json.dumps(result_dict, indent=2, default=str))
    else:
        _print_human(result_dict)



def _cmd_tool(args: argparse.Namespace) -> None:  # noqa: D401
    name = args.name
    tool = TOOL_REGISTRY.get(name)
    if tool is None:
        print(f"[ERROR] Tool '{name}' not found in registry", file=sys.stderr)
        sys.exit(1)

    try:
        kwargs = json.loads(args.kwargs or "{}")
    except json.JSONDecodeError as exc:  # pragma: no cover
        print(f"[ERROR] --kwargs must be valid JSON – {exc}", file=sys.stderr)
        sys.exit(1)

    # Convenience: if prompt/profile supplied at top-level, add
    if args.prompt:
        kwargs.setdefault("prompt", args.prompt)
    if args.profile:
        profile = _load_profile(args.user, args.profile)
        kwargs.setdefault("profile", profile)

    # Call tool (sync path)
    try:
        output = tool(**kwargs)  # type: ignore[arg-type]
    except Exception as exc:  # pragma: no cover
        print(f"[ERROR] Tool execution failed – {exc}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(output, indent=2, default=str))
    else:
        if isinstance(output, (dict, list)):
            print(json.dumps(output, indent=2))
        else:
            print(output)


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:  # noqa: D401
    parser = argparse.ArgumentParser(
        prog="essay-agent",
        description="Essay Agent – rich CLI interface for brainstorming through polishing",
    )

    parser.add_argument(
        "--debug", action="store_true", help="Enable verbose debug logging",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --------------------------- write -----------------------------------
    write = sub.add_parser("write", help="Run full essay workflow (brainstorm → polish)")
    write.add_argument("prompt_positional", nargs="*", help="Essay prompt – if omitted, use --prompt flag or interactive input")
    write.add_argument("--prompt", "-p", help="Essay prompt text (quoted)")
    write.add_argument("--word-limit", type=int, help="Word limit (default 650)")
    write.add_argument("--profile", help="Path to user profile JSON file")
    write.add_argument("--user", default="cli_user", help="User ID (default: cli_user)")
    write.add_argument("--json", action="store_true", help="Output JSON instead of human-readable text")
    write.add_argument(
        "--allow-demo",
        action="store_true",
        help="Allow offline demo run when OPENAI_API_KEY missing",
    )
    write.set_defaults(func=_cmd_write)

    # --------------------------- tool ------------------------------------
    tool = sub.add_parser("tool", help="Invoke a single registered tool by name")
    tool.add_argument("name", help="Tool name registered in TOOL_REGISTRY")
    tool.add_argument("--kwargs", help="JSON string with arguments for the tool")
    tool.add_argument("--prompt", help="Convenience flag – pass as 'prompt' kwarg")
    tool.add_argument("--profile", help="Path to profile JSON (passed as 'profile' kwarg)")
    tool.add_argument("--user", default="cli_user", help="User ID when loading profile")
    tool.add_argument("--json", action="store_true", help="JSON output")
    tool.set_defaults(func=_cmd_tool)

    return parser


def main(argv: Optional[list[str]] = None) -> None:  # noqa: D401
    parser = build_parser()
    args = parser.parse_args(argv)

    # Dispatch ------------------------------------------------------------
    if hasattr(args, "func"):
        args.func(args)
    else:  # pragma: no cover – should never happen due to required=True
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main() 