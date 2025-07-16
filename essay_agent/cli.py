import argparse
import asyncio
import dotenv
dotenv.load_dotenv()
import json
import os
import sys
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from essay_agent.agent_legacy import EssayAgent
from essay_agent.models import EssayPrompt
from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.memory.user_profile_schema import UserProfile
from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.utils.logging import debug_print
from essay_agent.eval import run_real_evaluation
from essay_agent.agent.core.react_agent import EssayReActAgent

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
# ReAct Agent Shortcuts System
# ---------------------------------------------------------------------------

class ReActShortcuts:
    """Shortcuts system for ReAct agent integration."""
    
    def __init__(self):
        self.shortcuts = {
            "ideas": {
                "message": "Help me brainstorm ideas for my essay",
                "description": "Brainstorm creative essay ideas"
            },
            "stories": {
                "message": "Help me think of personal stories I could write about",
                "description": "Generate personal story ideas"
            },
            "outline": {
                "message": "Help me create an outline for my essay",
                "description": "Create a structured essay outline"
            },
            "draft": {
                "message": "Help me write a draft of my essay",
                "description": "Generate essay draft content"
            },
            "revise": {
                "message": "Help me revise and improve my essay",
                "description": "Provide revision suggestions"
            },
            "polish": {
                "message": "Help me polish my essay for final submission",
                "description": "Final polishing and proofreading"
            },
            "status": {
                "message": "What's the current status of my essay work?",
                "description": "Check progress and next steps"
            },
            "help": {
                "message": "What can you help me with for my essay?",
                "description": "Show available assistance"
            }
        }
    
    def get_message_for_shortcut(self, shortcut: str) -> Optional[str]:
        """Get the message to send to the agent for a shortcut."""
        return self.shortcuts.get(shortcut, {}).get("message")
    
    def get_available_shortcuts(self) -> List[Dict[str, str]]:
        """Get list of available shortcuts with descriptions."""
        return [
            {"trigger": key, "description": value["description"]}
            for key, value in self.shortcuts.items()
        ]
    
    def format_shortcuts_help(self) -> str:
        """Format shortcuts help for display."""
        help_text = "🚀 Available shortcuts:\n\n"
        for shortcut, info in self.shortcuts.items():
            help_text += f"  {shortcut:<10} - {info['description']}\n"
        help_text += "\nUsage: essay-agent chat --shortcut <name>"
        return help_text

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

    # ------------------------------------------------------------------
    # Configure global logging flags ------------------------------------
    from essay_agent.utils import logging as elog
    elog.VERBOSE = bool(args.verbose)
    elog.JSON_MODE = bool(args.json)

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

    # Map --steps to Phase enum (if provided)
    from essay_agent.planner import Phase
    stop_phase = None
    if args.steps:
        mapping = {
            "brainstorm": Phase.BRAINSTORMING,
            "outline": Phase.OUTLINING,
            "draft": Phase.DRAFTING,
            "revise": Phase.REVISING,
            "polish": Phase.POLISHING,
        }
        stop_phase = mapping[args.steps]

    result = agent.run(essay_prompt, profile, debug=args.debug, stop_phase=stop_phase)

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
            print(json.dumps(output, indent=2, default=str))
        else:
            print(output)


def _cmd_eval(args: argparse.Namespace) -> None:  # noqa: D401
    """Run evaluation harness with real GPT calls."""
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        print("Please set your OpenAI API key:", file=sys.stderr)
        print("export OPENAI_API_KEY='your-api-key-here'", file=sys.stderr)
        sys.exit(1)
    
    try:
        results = run_real_evaluation(user_id=args.user, debug=args.debug)
        
        # Print summary stats
        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        pass_rate = passed_count / total_count if total_count > 0 else 0.0
        
        if args.json:
            # JSON output
            summary = {
                "total_tests": total_count,
                "passed": passed_count,
                "failed": total_count - passed_count,
                "pass_rate": pass_rate,
                "avg_execution_time": sum(r.execution_time for r in results) / len(results) if results else 0.0,
                "results": [asdict(r) for r in results]
            }
            print(json.dumps(summary, indent=2, default=str))
        else:
            # Human-readable output already printed by run_real_evaluation
            pass
        
        # Exit with appropriate code
        if pass_rate < 0.8:  # 80% pass rate threshold
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n🛑 Evaluation interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running evaluation: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


async def _cmd_chat(args: argparse.Namespace) -> None:  # noqa: D401
    """Handle 'essay-agent chat' command using ReAct agent."""
    
    # Check if API key is set for LLM responses
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        print("Please set your OpenAI API key:", file=sys.stderr)
        print("export OPENAI_API_KEY='your-api-key-here'", file=sys.stderr)
        sys.exit(1)
    
    # Handle shortcuts
    shortcuts = ReActShortcuts()
    
    # Show available shortcuts
    if hasattr(args, 'shortcuts') and args.shortcuts:
        print(shortcuts.format_shortcuts_help())
        return
    
    # Process shortcut command
    if hasattr(args, 'shortcut') and args.shortcut:
        shortcut_message = shortcuts.get_message_for_shortcut(args.shortcut)
        if shortcut_message:
            print(f"🚀 Executing shortcut: {args.shortcut}")
            print(f"   Message: {shortcut_message}")
            print()
            
            # Execute the shortcut using ReAct agent
            try:
                profile = _load_profile(args.user, args.profile)
                agent = EssayReActAgent(user_id=args.user)
                
                # Send the shortcut message
                response = await agent.handle_message(shortcut_message)
                print(f"🤖: {response}")
                
                # Ask if user wants to continue conversation
                print("\n" + "="*50)
                continue_chat = input("Continue conversation? (y/N): ").strip().lower()
                if continue_chat in ['y', 'yes']:
                    print()
                    await _start_react_conversation(agent, args)
                else:
                    print("🤖: Goodbye! Your conversation has been saved.")
                
            except Exception as e:
                print(f"❌ Error executing shortcut: {e}", file=sys.stderr)
                if hasattr(args, 'debug') and args.debug:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)
        else:
            print(f"❌ Unknown shortcut: {args.shortcut}")
            print("Available shortcuts:")
            available_shortcuts = shortcuts.get_available_shortcuts()
            for shortcut in available_shortcuts:
                print(f"  {shortcut['trigger']} - {shortcut['description']}")
            sys.exit(1)
        
        return
    
    # Normal conversation mode
    try:
        # Load user profile
        profile = _load_profile(args.user, args.profile)
        
        # Create ReAct agent
        agent = EssayReActAgent(user_id=args.user)
        
        # Start enhanced conversation
        await _start_react_conversation(agent, args)
        
    except KeyboardInterrupt:
        print("\n🤖: Goodbye! Your conversation has been saved.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting conversation: {e}", file=sys.stderr)
        if hasattr(args, 'debug') and args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


async def _start_react_conversation(agent: EssayReActAgent, args: argparse.Namespace) -> None:
    """Start enhanced conversation loop with ReAct agent."""
    print("🤖 Essay Agent Chat (Enhanced with ReAct Intelligence)")
    print("Tell me what you'd like to work on, and I'll help you with your essay!")
    print("Type 'help' for examples, 'status' for metrics, or 'quit' to exit.")
    print()
    
    try:
        while True:
            # Get user input with enhanced prompt
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle quit request
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("🤖: Goodbye! Your conversation has been saved.")
                break
            
            # Handle status request
            if user_input.lower() in ['status', 'metrics']:
                metrics = agent.get_session_metrics()
                print(f"📊 Session Statistics:")
                print(f"   Interactions: {metrics['interaction_count']}")
                print(f"   Average response time: {metrics['average_response_time']:.2f}s")
                print(f"   Session duration: {metrics['session_duration']:.1f}s")
                print()
                continue
            
            # Process through ReAct agent
            try:
                response = await agent.handle_message(user_input)
                print(f"🤖: {response}")
                print()
                
                # Show quick metrics if debug mode
                if hasattr(args, 'debug') and args.debug:
                    metrics = agent.get_session_metrics()
                    print(f"[Debug] Response time: {metrics['average_response_time']:.2f}s")
                    print()
                
            except Exception as e:
                print(f"🤖: I encountered an error: {e}")
                if hasattr(args, 'debug') and args.debug:
                    import traceback
                    traceback.print_exc()
                print("Let's try again. What would you like to work on?")
                print()
                continue
                
    except (KeyboardInterrupt, EOFError):
        print("\n🤖: Goodbye! Your conversation has been saved.")
    except Exception as e:
        print(f"🤖: I encountered an error: {e}")
        if hasattr(args, 'debug') and args.debug:
            import traceback
            traceback.print_exc()


def _cmd_agent_status(args: argparse.Namespace) -> None:  # noqa: D401
    """Show ReAct agent performance metrics and status."""
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Create agent to get metrics
        agent = EssayReActAgent(user_id=args.user)
        metrics = agent.get_session_metrics()
        
        if args.json:
            print(json.dumps(metrics, indent=2, default=str))
        else:
            print(f"📊 ReAct Agent Status for user: {args.user}")
            print(f"{'='*50}")
            print(f"Session Duration:     {metrics['session_duration']:.1f}s")
            print(f"Total Interactions:   {metrics['interaction_count']}")
            print(f"Average Response:     {metrics['average_response_time']:.2f}s")
            print(f"Total Response Time:  {metrics['total_response_time']:.2f}s")
            
            # Show reasoning metrics
            reasoning_metrics = metrics.get('reasoning_metrics', {})
            if reasoning_metrics:
                print(f"\n🧠 Reasoning Engine:")
                print(f"  Total Requests:     {reasoning_metrics.get('total_reasoning_requests', 0)}")
                print(f"  Successful:         {reasoning_metrics.get('successful_requests', 0)}")
                print(f"  Success Rate:       {reasoning_metrics.get('success_rate', 0):.1%}")
                print(f"  Avg Reasoning Time: {reasoning_metrics.get('average_reasoning_time', 0):.2f}s")
            
            # Show execution metrics
            execution_metrics = metrics.get('execution_metrics', {})
            if execution_metrics:
                print(f"\n⚙️ Action Executor:")
                print(f"  Total Executions:   {execution_metrics.get('total_executions', 0)}")
                print(f"  Successful:         {execution_metrics.get('successful_executions', 0)}")
                print(f"  Success Rate:       {execution_metrics.get('success_rate', 0):.1%}")
                print(f"  Avg Execution Time: {execution_metrics.get('average_execution_time', 0):.2f}s")
                
                # Show tool usage stats
                tool_stats = execution_metrics.get('tool_usage_stats', {})
                if tool_stats:
                    print(f"\n🔧 Tool Usage:")
                    for tool, stats in tool_stats.items():
                        print(f"  {tool}: {stats['usage_count']} uses, {stats['avg_time']:.2f}s avg")
            
            print(f"\n💡 Interactions per minute: {metrics.get('interactions_per_minute', 0):.1f}")
        
    except Exception as e:
        print(f"❌ Error getting agent status: {e}", file=sys.stderr)
        if hasattr(args, 'debug') and args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_agent_memory(args: argparse.Namespace) -> None:  # noqa: D401
    """Inspect agent memory and conversation history."""
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Create agent to access memory
        agent = EssayReActAgent(user_id=args.user)
        
        # Get recent conversation context
        context = agent._observe()
        
        if args.json:
            # Return structured memory data
            memory_data = {
                "user_id": args.user,
                "context": context,
                "recent_count": args.recent
            }
            print(json.dumps(memory_data, indent=2, default=str))
        else:
            print(f"🧠 Agent Memory for user: {args.user}")
            print(f"{'='*50}")
            
            # Show user profile
            user_profile = context.get('user_profile', {})
            if user_profile:
                print(f"👤 User Profile:")
                print(f"  User ID: {user_profile.get('user_id', 'Unknown')}")
                if 'name' in user_profile:
                    print(f"  Name: {user_profile['name']}")
                print()
            
            # Show conversation history
            conversation_history = context.get('conversation_history', [])
            if conversation_history:
                print(f"💬 Recent Conversations ({min(len(conversation_history), args.recent)} of {len(conversation_history)}):")
                for i, turn in enumerate(conversation_history[-args.recent:], 1):
                    if isinstance(turn, dict):
                        user_msg = turn.get('user_input', 'N/A')[:100]
                        agent_msg = turn.get('agent_response', 'N/A')[:100]
                        print(f"  {i}. You: {user_msg}{'...' if len(str(turn.get('user_input', ''))) > 100 else ''}")
                        print(f"     🤖: {agent_msg}{'...' if len(str(turn.get('agent_response', ''))) > 100 else ''}")
                        print()
                print()
            
            # Show essay state
            essay_state = context.get('essay_state', {})
            if essay_state:
                print(f"📝 Essay State:")
                for key, value in essay_state.items():
                    if value:
                        print(f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                print()
            
            # Show memory patterns
            patterns = context.get('patterns', [])
            if patterns:
                print(f"🔍 Memory Patterns:")
                for pattern in patterns[:5]:  # Show first 5 patterns
                    print(f"  • {pattern}")
                if len(patterns) > 5:
                    print(f"  ... and {len(patterns) - 5} more")
                print()
            
            # Show session info
            session_info = context.get('session_info', {})
            if session_info:
                print(f"📊 Session Info:")
                print(f"  Interactions: {session_info.get('interaction_count', 0)}")
                print(f"  Duration: {session_info.get('session_duration', 0):.1f}s")
                print(f"  Avg Response: {session_info.get('avg_response_time', 0):.2f}s")
        
    except Exception as e:
        print(f"❌ Error accessing agent memory: {e}", file=sys.stderr)
        if hasattr(args, 'debug') and args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_agent_debug(args: argparse.Namespace) -> None:  # noqa: D401
    """Debug ReAct agent reasoning and execution."""
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Create agent to access debug info
        agent = EssayReActAgent(user_id=args.user)
        
        debug_info = {
            "user_id": args.user,
            "reasoning_metrics": agent.reasoning_engine.get_performance_metrics(),
            "execution_metrics": agent.action_executor.get_performance_metrics(),
            "session_metrics": agent.get_session_metrics()
        }
        
        if args.json:
            print(json.dumps(debug_info, indent=2, default=str))
        else:
            print(f"🔧 ReAct Agent Debug Info for user: {args.user}")
            print(f"{'='*60}")
            
            # Show reasoning engine details
            reasoning_metrics = debug_info['reasoning_metrics']
            print(f"🧠 Reasoning Engine Debug:")
            print(f"  Total reasoning requests: {reasoning_metrics.get('total_reasoning_requests', 0)}")
            print(f"  Successful requests:      {reasoning_metrics.get('successful_requests', 0)}")
            print(f"  Success rate:             {reasoning_metrics.get('success_rate', 0):.1%}")
            print(f"  Average reasoning time:   {reasoning_metrics.get('average_reasoning_time', 0):.3f}s")
            print(f"  Total reasoning time:     {reasoning_metrics.get('total_reasoning_time', 0):.2f}s")
            print()
            
            # Show action executor details
            execution_metrics = debug_info['execution_metrics']
            print(f"⚙️ Action Executor Debug:")
            print(f"  Total executions:         {execution_metrics.get('total_executions', 0)}")
            print(f"  Successful executions:    {execution_metrics.get('successful_executions', 0)}")
            print(f"  Success rate:             {execution_metrics.get('success_rate', 0):.1%}")
            print(f"  Average execution time:   {execution_metrics.get('average_execution_time', 0):.3f}s")
            print(f"  Total execution time:     {execution_metrics.get('total_execution_time', 0):.2f}s")
            print()
            
            # Show tool usage statistics
            tool_stats = execution_metrics.get('tool_usage_stats', {})
            if tool_stats:
                print(f"🔧 Tool Usage Statistics:")
                for tool_name, stats in tool_stats.items():
                    print(f"  {tool_name}:")
                    print(f"    Usage count:    {stats.get('usage_count', 0)}")
                    print(f"    Success count:  {stats.get('success_count', 0)}")
                    print(f"    Average time:   {stats.get('avg_time', 0):.3f}s")
                    print(f"    Total time:     {stats.get('total_time', 0):.2f}s")
                    print()
            
            # Show session summary
            session_metrics = debug_info['session_metrics']
            print(f"📊 Session Summary:")
            print(f"  Session duration:         {session_metrics.get('session_duration', 0):.1f}s")
            print(f"  Total interactions:       {session_metrics.get('interaction_count', 0)}")
            print(f"  Interactions per minute:  {session_metrics.get('interactions_per_minute', 0):.1f}")
            print(f"  Average response time:    {session_metrics.get('average_response_time', 0):.3f}s")
        
    except Exception as e:
        print(f"❌ Error getting debug info: {e}", file=sys.stderr)
        if hasattr(args, 'debug') and args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


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
    write.add_argument("--verbose", action="store_true", help="Stream per-tool trace output")
    write.add_argument("--steps", choices=["brainstorm", "outline", "draft", "revise", "polish"], help="Run only up to the specified phase")
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

    # --------------------------- eval ------------------------------------
    eval_cmd = sub.add_parser("eval", help="Run evaluation harness with real GPT calls")
    eval_cmd.add_argument("--user", default="real_eval_user", help="User ID for evaluation (default: real_eval_user)")
    eval_cmd.add_argument("--json", action="store_true", help="Output JSON instead of human-readable text")
    eval_cmd.set_defaults(func=_cmd_eval)

    # --------------------------- chat ------------------------------------
    chat = sub.add_parser("chat", help="Enter conversational mode with ReAct agent")
    chat.add_argument("--user", default="cli_user", help="User ID (default: cli_user)")
    chat.add_argument("--profile", help="Path to user profile JSON file")
    chat.add_argument("--shortcut", choices=["ideas", "stories", "outline", "draft", "revise", "polish", "status", "help"], 
                  help="Start conversation with a shortcut (e.g., 'outline', 'draft')")
    chat.add_argument("--shortcuts", action="store_true", help="Show available shortcuts")
    chat.set_defaults(func=_cmd_chat)

    # --------------------------- agent-status ------------------------------
    agent_status = sub.add_parser("agent-status", help="Show ReAct agent performance metrics")
    agent_status.add_argument("--user", default="cli_user", help="User ID (default: cli_user)")
    agent_status.add_argument("--json", action="store_true", help="Output JSON format")
    agent_status.set_defaults(func=_cmd_agent_status)

    # --------------------------- agent-memory ------------------------------
    agent_memory = sub.add_parser("agent-memory", help="Inspect agent memory and conversation history") 
    agent_memory.add_argument("--user", default="cli_user", help="User ID (default: cli_user)")
    agent_memory.add_argument("--recent", type=int, default=10, help="Number of recent interactions to show")
    agent_memory.add_argument("--json", action="store_true", help="Output JSON format")
    agent_memory.set_defaults(func=_cmd_agent_memory)

    # --------------------------- agent-debug -------------------------------
    agent_debug = sub.add_parser("agent-debug", help="Debug ReAct agent reasoning")
    agent_debug.add_argument("--user", default="cli_user", help="User ID (default: cli_user)")
    agent_debug.add_argument("--last-interaction", action="store_true", help="Show last interaction details")
    agent_debug.add_argument("--reasoning-chain", action="store_true", help="Show reasoning chain")
    agent_debug.add_argument("--json", action="store_true", help="Output JSON format")
    agent_debug.set_defaults(func=_cmd_agent_debug)

    return parser


def main(argv: Optional[list[str]] = None) -> None:  # noqa: D401
    parser = build_parser()
    args = parser.parse_args(argv)

    # Dispatch ------------------------------------------------------------
    if hasattr(args, "func"):
        # Handle async commands
        if args.func == _cmd_chat:
            import asyncio
            asyncio.run(args.func(args))
        else:
            args.func(args)
    else:  # pragma: no cover – should never happen due to required=True
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main() 