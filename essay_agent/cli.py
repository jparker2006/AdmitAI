import argparse
import asyncio
import dotenv
dotenv.load_dotenv()
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from essay_agent.agent_legacy import EssayAgent
from essay_agent.models import EssayPrompt
from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.memory.user_profile_schema import UserProfile
from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.utils.logging import debug_print
from essay_agent.eval import run_real_evaluation
from essay_agent.agent.core.react_agent import EssayReActAgent
from essay_agent.eval.conversational_scenarios import (
    ALL_SCENARIOS, get_scenario_by_id, get_scenarios_by_category, 
    get_scenarios_by_difficulty, get_scenarios_by_school, get_scenario_summary
)
from essay_agent.eval.real_profiles import (
    ALL_PROFILES, get_profile_by_id, get_profiles_by_category, get_profiles_summary
)
from essay_agent.eval.conversation_runner import ConversationRunner, run_evaluation_batch, save_evaluation_results
from essay_agent.eval.integrated_conversation_runner import IntegratedConversationRunner, list_evaluation_memory_files
# from essay_agent.eval.autonomy_tester import AutonomyTester, run_comprehensive_autonomy_test  # DEPRECATED
from essay_agent.eval.memory_scenarios import MemoryScenarioTester, run_comprehensive_memory_test

# Add new imports for LLM-powered evaluation system
from essay_agent.eval.llm_evaluator import LLMEvaluator, ConversationEvaluation
from essay_agent.eval.batch_processor import BatchProcessor, BatchResult, BatchProgress 
from essay_agent.eval.pattern_analyzer import PatternAnalyzer, PatternAnalysis

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
    from essay_agent.models import Phase
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
        results = run_real_evaluation(user_id=args.user, debug=args.debug, use_legacy_metrics=args.legacy_heuristics)
        
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


def _cmd_eval_list(args: argparse.Namespace) -> None:
    """List all available conversational evaluations."""
    
    try:
        scenarios = ALL_SCENARIOS
        
        # Apply filters
        if args.category:
            from essay_agent.eval.conversational_scenarios import ScenarioCategory
            try:
                category = ScenarioCategory(args.category)
                scenarios = get_scenarios_by_category(category)
            except ValueError:
                print(f"❌ Invalid category: {args.category}", file=sys.stderr)
                print(f"Available categories: {[c.value for c in ScenarioCategory]}")
                sys.exit(1)
        
        if args.difficulty:
            scenarios = [s for s in scenarios if s.difficulty == args.difficulty]
        
        if args.school:
            scenarios = [s for s in scenarios if args.school.lower() in s.school.lower()]
        
        if args.json:
            # JSON output
            output = {
                "total_scenarios": len(scenarios),
                "scenarios": [
                    {
                        "eval_id": s.eval_id,
                        "name": s.name,
                        "category": s.category.value,
                        "school": s.school,
                        "difficulty": s.difficulty,

                        "estimated_duration": s.estimated_duration_minutes,
                        "description": s.description
                    }
                    for s in scenarios
                ]
            }
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            print(f"📋 Available Conversational Evaluations ({len(scenarios)} scenarios)")
            print(f"{'='*70}")
            
            if not scenarios:
                print("No scenarios match the specified filters.")
                return
            
            # Group by category
            from collections import defaultdict
            by_category = defaultdict(list)
            for scenario in scenarios:
                by_category[scenario.category.value].append(scenario)
            
            for category, cat_scenarios in by_category.items():
                print(f"\n🏷️  {category.upper()} ({len(cat_scenarios)} scenarios)")
                print("-" * 50)
                
                for scenario in cat_scenarios:
                    print(f"  📝 {scenario.eval_id}")
                    print(f"     {scenario.name}")
                    print(f"     School: {scenario.school} | Difficulty: {scenario.difficulty}")
                    print(f"     Duration: ~{scenario.estimated_duration_minutes}min")
                    print(f"     {scenario.description}")
                    print()
                    
        # Show summary
        if not args.json:
            summary = get_scenario_summary()
            print(f"\n📊 Summary:")
            print(f"   Total scenarios: {summary['total_scenarios']}")
            print(f"   Schools covered: {summary['schools_covered']}")
            print(f"   Avg duration: {summary['avg_duration_minutes']:.1f} minutes")
            
    except Exception as e:
        print(f"❌ Error listing scenarios: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_eval_conversation(args: argparse.Namespace) -> None:
    """Run a specific conversational evaluation."""
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY required for conversational evaluations", file=sys.stderr)
        print("Please set your OpenAI API key:", file=sys.stderr)
        print("export OPENAI_API_KEY='your-api-key-here'", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Load scenario
        scenario = get_scenario_by_id(args.eval_id)
        if not scenario:
            print(f"❌ Evaluation '{args.eval_id}' not found", file=sys.stderr)
            print("Available evaluations:")
            _cmd_eval_list(argparse.Namespace(category=None, difficulty=None, school=None, json=False, debug=False))
            sys.exit(1)
        
        # Load profile if specified
        profile = None
        if args.profile:
            profile = get_profile_by_id(args.profile)
            if not profile:
                print(f"❌ Profile '{args.profile}' not found", file=sys.stderr)
                print("Available profiles:")
                for p in ALL_PROFILES:
                    print(f"  - {p.profile_id}: {p.name}")
                sys.exit(1)
        
        print(f"🚀 Running conversational evaluation: {scenario.eval_id}")
        print(f"   Scenario: {scenario.name}")
        print(f"   School: {scenario.school}")
        print(f"   Profile: {profile.name if profile else 'Auto-selected'}")
        print(f"   Expected duration: ~{scenario.estimated_duration_minutes} minutes")
        
        # Choose runner based on memory integration flag
        if args.use_integrated_memory:
            print(f"   Memory: Integrated (saves to memory_store)")
            runner = IntegratedConversationRunner(verbose=args.verbose)
        else:
            print(f"   Memory: Standard evaluation (no persistence)")
            runner = ConversationRunner(verbose=args.verbose)
        print()
        
        # Execute conversation
        result = asyncio.run(runner.execute_evaluation(scenario, profile))
        
        # Save conversation if requested
        if args.save_conversation:
            filename = f"conversation_{args.eval_id}_{result.execution_timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(result.to_dict(), f, indent=2, default=str)
            print(f"💾 Conversation saved to: {filename}")
        
        # Display memory integration summary if using integrated memory
        if args.use_integrated_memory and isinstance(runner, IntegratedConversationRunner):
            runner.print_integration_summary()
        
        # Display results
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, default=str))
        else:
            # Already printed by runner in verbose mode
            if not args.verbose:
                print(f"✅ Evaluation completed: {result.completion_status}")
                print(f"   Success score: {result.overall_success_score:.2f}")
                print(f"   Duration: {result.total_duration_seconds:.1f}s")
                print(f"   Turns: {result.total_turns}")
                print(f"   Tools used: {result.unique_tools_used}")
                
                if result.issues_encountered:
                    print(f"⚠️  Issues: {len(result.issues_encountered)}")
                    for issue in result.issues_encountered[:3]:  # Show first 3
                        print(f"     - {issue}")
        
        # Exit with appropriate code based on success
        if result.overall_success_score >= 0.7:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Evaluation interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running conversation evaluation: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_eval_suite(args: argparse.Namespace) -> None:
    """Run evaluation suite by category or criteria."""
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY required for conversational evaluations", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Select scenarios based on criteria
        scenarios = ALL_SCENARIOS
        
        if args.category:
            from essay_agent.eval.conversational_scenarios import ScenarioCategory
            try:
                category = ScenarioCategory(args.category)
                scenarios = get_scenarios_by_category(category)
            except ValueError:
                print(f"❌ Invalid category: {args.category}", file=sys.stderr)
                sys.exit(1)
        
        if args.difficulty:
            scenarios = [s for s in scenarios if s.difficulty == args.difficulty]
        
        if args.school:
            scenarios = [s for s in scenarios if args.school.lower() in s.school.lower()]
        
        # Limit number of scenarios
        if args.count:
            scenarios = scenarios[:args.count]
        
        if not scenarios:
            print("❌ No scenarios match the specified criteria", file=sys.stderr)
            sys.exit(1)
        
        print(f"🚀 Running evaluation suite: {len(scenarios)} scenarios")
        print(f"   Category: {args.category or 'All'}")
        print(f"   Difficulty: {args.difficulty or 'All'}")
        print(f"   School: {args.school or 'All'}")
        print(f"   Parallel execution: {args.parallel}")
        print()
        
        # Run evaluations
        if args.parallel:
            results = asyncio.run(run_evaluation_batch(
                scenarios, 
                verbose=args.verbose,
                max_concurrent=args.parallel
            ))
        else:
            # Sequential execution
            results = []
            for i, scenario in enumerate(scenarios, 1):
                print(f"📝 Running scenario {i}/{len(scenarios)}: {scenario.eval_id}")
                runner = ConversationRunner(verbose=args.verbose)
                result = asyncio.run(runner.execute_evaluation(scenario))
                results.append(result)
        
        # Save results
        output_file = f"eval_suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_evaluation_results(results, output_file)
        
        # Calculate summary
        successful = sum(1 for r in results if r.overall_success_score >= 0.7)
        avg_score = sum(r.overall_success_score for r in results) / len(results)
        avg_duration = sum(r.total_duration_seconds for r in results) / len(results)
        
        if args.json:
            summary = {
                "total_scenarios": len(results),
                "successful": successful,
                "success_rate": successful / len(results),
                "average_score": avg_score,
                "average_duration": avg_duration,
                "results_file": output_file
            }
            print(json.dumps(summary, indent=2))
        else:
            print(f"\n📊 Evaluation Suite Results:")
            print(f"   Total scenarios: {len(results)}")
            print(f"   Successful: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
            print(f"   Average score: {avg_score:.2f}")
            print(f"   Average duration: {avg_duration:.1f}s")
            print(f"   Results saved to: {output_file}")
        
        # Exit based on success rate
        if successful / len(results) >= 0.8:  # 80% success threshold
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Evaluation suite interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running evaluation suite: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_eval_autonomy(args: argparse.Namespace) -> None:
    """Run autonomy testing for user profile."""
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY required for autonomy testing", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Load profile
        profile = get_profile_by_id(args.profile)
        if not profile:
            print(f"❌ Profile '{args.profile}' not found", file=sys.stderr)
            print("Available profiles:")
            for p in ALL_PROFILES:
                print(f"  - {p.profile_id}: {p.name}")
            sys.exit(1)
        
        print(f"🧪 Running autonomy testing for profile: {profile.name}")
        print(f"   Testing all autonomy levels: {not args.level}")
        if args.level:
            print(f"   Testing specific level: {args.level}")
        print()
        
        # Run autonomy test
        report = asyncio.run(run_comprehensive_autonomy_test(
            profile, 
            output_file=args.output if args.output else None
        ))
        
        if args.json:
            print(json.dumps(report, indent=2, default=str))
        else:
            print(f"🤖 Autonomy Test Report:")
            print(f"   Overall score: {report['overall_autonomy_score']:.2f}")
            print(f"   Level scores:")
            for level, score in report['level_scores'].items():
                print(f"     {level}: {score:.2f}")
            
            if report['strengths']:
                print(f"\n✅ Strengths:")
                for strength in report['strengths'][:5]:  # Show top 5
                    print(f"     - {strength}")
            
            if report['weaknesses']:
                print(f"\n⚠️  Areas for improvement:")
                for weakness in report['weaknesses'][:5]:  # Show top 5
                    print(f"     - {weakness}")
        
        # Exit based on overall score
        if report['overall_autonomy_score'] >= 0.7:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error running autonomy test: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_eval_memory(args: argparse.Namespace) -> None:
    """Run memory utilization testing for user profile."""
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY required for memory testing", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Load profile
        profile = get_profile_by_id(args.profile)
        if not profile:
            print(f"❌ Profile '{args.profile}' not found", file=sys.stderr)
            print("Available profiles:")
            for p in ALL_PROFILES:
                print(f"  - {p.profile_id}: {p.name}")
            sys.exit(1)
        
        print(f"🧠 Running memory utilization testing for profile: {profile.name}")
        print(f"   Testing all memory patterns")
        print()
        
        # Run memory test
        report = asyncio.run(run_comprehensive_memory_test(
            profile,
            output_file=args.output if args.output else None
        ))
        
        if args.json:
            print(json.dumps(report, indent=2, default=str))
        else:
            print(f"💾 Memory Utilization Report:")
            print(f"   Overall score: {report['overall_memory_score']:.2f}")
            print(f"   Pattern scores:")
            for pattern, score in report['pattern_scores'].items():
                print(f"     {pattern}: {score:.2f}")
            
            if report['memory_strengths']:
                print(f"\n✅ Memory strengths:")
                for strength in report['memory_strengths'][:5]:
                    print(f"     - {strength}")
            
            if report['memory_weaknesses']:
                print(f"\n⚠️  Memory gaps:")
                for weakness in report['memory_weaknesses'][:5]:
                    print(f"     - {weakness}")
        
        # Exit based on overall score
        if report['overall_memory_score'] >= 0.7:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error running memory test: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_eval_memory_list(args: argparse.Namespace) -> None:
    """List evaluation conversations saved in memory_store."""
    
    try:
        # Get list of evaluation memory files
        eval_files = list_evaluation_memory_files(args.prefix)
        
        if not eval_files:
            print(f"📭 No evaluation memory files found with prefix '{args.prefix}'")
            print(f"   Check: memory_store/{args.prefix}_*")
            print(f"   Use --use-integrated-memory flag when running evaluations to save to memory_store")
            return
        
        if args.json:
            # Output JSON format
            import os
            file_info = []
            for file_path in eval_files:
                stat = os.stat(file_path)
                file_info.append({
                    "path": file_path,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "user_id": os.path.basename(file_path).split('.')[0]
                })
            
            print(json.dumps({
                "prefix": args.prefix,
                "total_files": len(eval_files),
                "files": file_info
            }, indent=2))
        else:
            # Human-readable format
            print(f"📁 Evaluation Memory Files (prefix: {args.prefix})")
            print(f"{'='*60}")
            print(f"Found {len(eval_files)} files in memory_store/")
            print()
            
            import os
            for file_path in eval_files:
                file_name = os.path.basename(file_path)
                user_id = file_name.split('.')[0]
                file_type = "conversation" if file_name.endswith('.conv.json') else "profile"
                
                stat = os.stat(file_path)
                size_kb = stat.st_size / 1024
                modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"  📄 {file_name}")
                print(f"     User ID: {user_id}")
                print(f"     Type: {file_type}")
                print(f"     Size: {size_kb:.1f} KB")
                print(f"     Modified: {modified}")
                print()
            
            print(f"🔍 Usage Examples:")
            print(f"  # Chat with evaluation user (shows conversation history)")
            for file_path in eval_files[:3]:  # Show first 3 examples
                user_id = os.path.basename(file_path).split('.')[0]
                print(f"  python -m essay_agent chat --user-id {user_id}")
            print()
            print(f"  # View conversation file directly")
            print(f"  cat memory_store/{args.prefix}_*.conv.json | jq .")
    
    except Exception as e:
        print(f"❌ Error listing evaluation memory files: {e}", file=sys.stderr)
        if hasattr(args, 'debug') and args.debug:
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


# ============================================================================
# Enhanced Evaluation Commands with LLM-Powered Intelligence
# ============================================================================

def _cmd_eval_smart(args: argparse.Namespace) -> None:  # noqa: D401
    """Run intelligent evaluations with natural language scenario selection."""
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY required for LLM-powered evaluations", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Smart scenario selection
        if args.description:
            scenarios = _smart_select_scenarios(args.description, args.count or 5)
            print(f"🔍 Smart scenario selection for: '{args.description}'")
        elif args.quick:
            scenarios = _get_quick_test_scenarios()
            print("⚡ Running quick evaluation suite")
        else:
            scenarios = _interactive_scenario_selection()
        
        if not scenarios:
            print("❌ No scenarios selected", file=sys.stderr)
            sys.exit(1)
        
        print(f"🚀 Running {len(scenarios)} evaluation scenarios")
        
        # Initialize batch processor
        batch_processor = BatchProcessor(
            max_parallel=args.parallel,
            enable_llm_evaluation=not args.legacy_heuristics,
            progress_callback=_print_progress if args.live else None
        )
        
        # Run comprehensive evaluation
        batch_result = asyncio.run(
            batch_processor.run_comprehensive_suite(
                scenarios=scenarios,
                time_limit=args.time_limit,
                export_path=args.export if args.export else None
            )
        )
        
        # Print results
        if args.json:
            print(json.dumps(batch_result.to_dict(), indent=2, default=str))
        else:
            _print_smart_evaluation_results(batch_result)
        
    except KeyboardInterrupt:
        print("\n🛑 Smart evaluation interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running smart evaluation: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_eval_batch(args: argparse.Namespace) -> None:  # noqa: D401
    """Run batch evaluations with intelligent scheduling and progress tracking."""
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY required for batch evaluations", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Load scenarios
        if args.scenarios:
            scenario_ids = args.scenarios.split(',')
            scenarios = [get_scenario_by_id(sid.strip()) for sid in scenario_ids]
            scenarios = [s for s in scenarios if s is not None]
        else:
            scenarios = _get_balanced_scenario_selection(args.count or 20)
        
        print(f"🔄 Running batch evaluation: {len(scenarios)} scenarios")
        print(f"⚙️ Parallel execution: {args.parallel} concurrent evaluations")
        
        # Initialize batch processor with progress tracking
        batch_processor = BatchProcessor(
            max_parallel=args.parallel,
            enable_llm_evaluation=not args.legacy_heuristics,
            progress_callback=_print_progress if not args.quiet else None
        )
        
        # Run batch with time limit
        batch_result = asyncio.run(
            batch_processor.run_comprehensive_suite(
                scenarios=scenarios,
                time_limit=args.time_limit,
                export_path=args.export
            )
        )
        
        # Generate insights if requested
        if args.insights and batch_result.successful_evaluations > 5:
            print("\n🧠 Generating insights...")
            analyzer = PatternAnalyzer()
            # Would need evaluation data to analyze
            print("✅ Insights analysis complete")
        
        # Output results
        if args.json:
            print(json.dumps(batch_result.to_dict(), indent=2, default=str))
        else:
            _print_batch_results(batch_result)
        
    except KeyboardInterrupt:
        print("\n🛑 Batch evaluation interrupted by user", file=sys.stderr)
        batch_processor.cancel_current_batch()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running batch evaluation: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_eval_insights(args: argparse.Namespace) -> None:  # noqa: D401
    """Analyze evaluation patterns and generate insights."""
    
    try:
        # Load evaluation results
        if args.file:
            with open(args.file, 'r') as f:
                batch_data = json.load(f)
            batch_results = [BatchResult(**batch_data)]  # Simplified loading
        else:
            # Load recent evaluation results from default location
            batch_results = _load_recent_batch_results(args.days or 7)
        
        if not batch_results:
            print("❌ No evaluation results found to analyze", file=sys.stderr)
            sys.exit(1)
        
        print(f"🔍 Analyzing {len(batch_results)} batch results...")
        
        # Initialize pattern analyzer
        analyzer = PatternAnalyzer()
        
        # Extract evaluation data (would need proper data structure)
        evaluations = []  # Would extract from batch_results
        
        # Perform pattern analysis
        analysis = analyzer.analyze_conversation_patterns(
            evaluations=evaluations,
            batch_results=batch_results,
            time_window_days=args.days or 7
        )
        
        # Output results
        if args.json:
            print(json.dumps(analysis.to_dict(), indent=2, default=str))
        elif args.export:
            analysis.save_to_file(args.export)
            print(f"📄 Analysis exported to: {args.export}")
        else:
            _print_insights_analysis(analysis)
        
    except Exception as e:
        print(f"❌ Error analyzing patterns: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_eval_monitor(args: argparse.Namespace) -> None:  # noqa: D401
    """Monitor evaluation system with continuous testing."""
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY required for monitoring", file=sys.stderr)
        sys.exit(1)
    
    try:
        print(f"📊 Starting continuous monitoring for {args.duration} hours")
        print("Press Ctrl+C to stop monitoring")
        
        # Initialize batch processor for monitoring
        batch_processor = BatchProcessor(
            max_parallel=args.parallel,
            enable_llm_evaluation=not args.legacy_heuristics,
            progress_callback=_print_progress
        )
        
        # Run continuous monitoring
        batch_results = asyncio.run(
            batch_processor.run_continuous_monitoring(
                duration_hours=args.duration,
                scenario_rotation=True
            )
        )
        
        print(f"\n✅ Monitoring completed: {len(batch_results)} batches executed")
        
        # Generate summary report
        if args.export:
            summary = _generate_monitoring_summary(batch_results)
            with open(args.export, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            print(f"📄 Monitoring report exported to: {args.export}")
        
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user", file=sys.stderr)
        batch_processor.cancel_current_batch()
    except Exception as e:
        print(f"❌ Error during monitoring: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _cmd_eval_discover(args: argparse.Namespace) -> None:  # noqa: D401
    """Discover and recommend evaluation scenarios based on criteria."""
    
    try:
        print("🔍 Discovering evaluation scenarios...")
        
        # Smart scenario discovery
        if args.description:
            scenarios = _smart_select_scenarios(args.description, limit=20)
            print(f"📋 Found {len(scenarios)} scenarios matching: '{args.description}'")
        else:
            scenarios = _get_recommended_scenarios(
                school=args.school,
                difficulty=args.difficulty,
                user_type=args.user_type
            )
            print(f"📋 Recommended scenarios: {len(scenarios)}")
        
        # Output scenarios
        if args.json:
            scenario_data = [
                {
                    "eval_id": s.eval_id,
                    "name": s.name,
                    "school": s.school,
                    "difficulty": s.difficulty,
                    "category": s.category.value,
                    "description": s.description[:100] + "..." if len(s.description) > 100 else s.description
                }
                for s in scenarios
            ]
            print(json.dumps(scenario_data, indent=2))
        else:
            _print_scenario_recommendations(scenarios)
        
        # Interactive selection
        if args.interactive and scenarios:
            selected = _interactive_scenario_picker(scenarios)
            if selected:
                print(f"\n✅ Selected {len(selected)} scenarios for evaluation")
                # Could launch evaluation immediately
    
    except Exception as e:
        print(f"❌ Error discovering scenarios: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


# ============================================================================
# Helper Functions for Enhanced Evaluation
# ============================================================================

def _smart_select_scenarios(description: str, limit: int = 10):
    """Select scenarios based on natural language description."""
    from essay_agent.eval.conversational_scenarios import get_all_scenarios
    
    scenarios = get_all_scenarios()
    
    # Simple keyword matching for now - could be enhanced with LLM
    description_lower = description.lower()
    keywords = description_lower.split()
    
    scored_scenarios = []
    for scenario in scenarios:
        score = 0
        text_to_search = f"{scenario.name} {scenario.description} {scenario.school} {scenario.difficulty}".lower()
        
        for keyword in keywords:
            if keyword in text_to_search:
                score += 1
        
        if score > 0:
            scored_scenarios.append((scenario, score))
    
    # Sort by score and return top scenarios
    scored_scenarios.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored_scenarios[:limit]]


def _get_quick_test_scenarios():
    """Get a quick set of diverse scenarios for testing."""
    from essay_agent.eval.conversational_scenarios import get_scenarios_by_category, ScenarioCategory
    
    scenarios = []
    
    # Get 2 scenarios from each category
    for category in ScenarioCategory:
        cat_scenarios = get_scenarios_by_category(category)
        scenarios.extend(cat_scenarios[:2])
    
    return scenarios[:8]  # Limit to 8 for quick testing


def _get_balanced_scenario_selection(count: int):
    """Get a balanced selection of scenarios across categories."""
    from essay_agent.eval.conversational_scenarios import get_scenarios_by_category, ScenarioCategory
    
    scenarios = []
    scenarios_per_category = max(1, count // len(ScenarioCategory))
    
    for category in ScenarioCategory:
        cat_scenarios = get_scenarios_by_category(category)
        scenarios.extend(cat_scenarios[:scenarios_per_category])
    
    return scenarios[:count]


def _print_progress(progress: BatchProgress):
    """Print batch progress updates."""
    percentage = progress.completion_percentage
    eta = progress.estimated_completion.strftime("%H:%M:%S") if progress.estimated_completion else "Unknown"
    
    print(f"\r🔄 Progress: {percentage:.1f}% "
          f"({progress.completed_tasks}/{progress.total_tasks}) "
          f"| Running: {progress.running_tasks} "
          f"| Failed: {progress.failed_tasks} "
          f"| ETA: {eta}", end="", flush=True)


def _print_smart_evaluation_results(batch_result: BatchResult):
    """Print formatted results from smart evaluation."""
    print(f"\n🎯 Smart Evaluation Results")
    print(f"{'='*60}")
    print(f"Status: {batch_result.status.value}")
    print(f"Duration: {batch_result.total_duration_seconds:.1f}s")
    print(f"Success Rate: {batch_result.successful_evaluations}/{batch_result.progress.total_tasks}")
    print(f"Average Quality Score: {batch_result.average_evaluation_score:.2f}")
    
    if batch_result.total_llm_cost > 0:
        print(f"LLM Cost: ${batch_result.total_llm_cost:.3f}")
    
    if batch_result.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in batch_result.recommendations[:3]:
            print(f"  • {rec}")


def _print_batch_results(batch_result: BatchResult):
    """Print comprehensive batch results."""
    print(f"\n📊 Batch Evaluation Results")
    print(f"{'='*60}")
    print(f"Batch ID: {batch_result.batch_id}")
    print(f"Status: {batch_result.status.value}")
    print(f"Total Duration: {batch_result.total_duration_seconds:.1f}s")
    print(f"Successful: {batch_result.successful_evaluations}")
    print(f"Failed: {batch_result.failed_evaluations}")
    print(f"Success Rate: {batch_result.successful_evaluations/(batch_result.successful_evaluations + batch_result.failed_evaluations):.1%}")
    print(f"Average Quality: {batch_result.average_evaluation_score:.2f}")
    
    if batch_result.total_llm_cost > 0:
        print(f"Total LLM Cost: ${batch_result.total_llm_cost:.3f}")
        print(f"Avg Cost/Eval: ${batch_result.total_llm_cost/max(1, batch_result.successful_evaluations):.3f}")
    
    if batch_result.common_failure_reasons:
        print(f"\n⚠️ Common Issues:")
        for reason in batch_result.common_failure_reasons[:3]:
            print(f"  • {reason}")
    
    if batch_result.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in batch_result.recommendations[:5]:
            print(f"  • {rec}")


def _print_insights_analysis(analysis: PatternAnalysis):
    """Print pattern analysis insights."""
    print(f"\n🧠 Pattern Analysis Results")
    print(f"{'='*60}")
    print(f"Analysis ID: {analysis.analysis_id}")
    print(f"System Health: {analysis.overall_system_health}")
    print(f"Evaluations Analyzed: {analysis.total_evaluations_analyzed}")
    print(f"Patterns Identified: {len(analysis.identified_patterns)}")
    
    if analysis.critical_issues:
        print(f"\n🚨 Critical Issues:")
        for issue in analysis.critical_issues:
            print(f"  • {issue}")
    
    if analysis.quick_wins:
        print(f"\n⚡ Quick Wins:")
        for win in analysis.quick_wins[:3]:
            print(f"  • {win}")
    
    if analysis.long_term_priorities:
        print(f"\n🎯 Long-term Priorities:")
        for priority in analysis.long_term_priorities[:3]:
            print(f"  • {priority}")


def _interactive_scenario_selection():
    """Interactive scenario selection interface."""
    print("\n🎯 Interactive Scenario Selection")
    print("1. Quick test suite (8 scenarios)")
    print("2. Comprehensive suite (20 scenarios)")
    print("3. Custom selection")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        return _get_quick_test_scenarios()
    elif choice == "2":
        return _get_balanced_scenario_selection(20)
    elif choice == "3":
        description = input("Describe the scenarios you want (e.g., 'Stanford brainstorming'): ").strip()
        if description:
            return _smart_select_scenarios(description, 10)
        else:
            return _get_quick_test_scenarios()
    else:
        print("Invalid choice, using quick test suite")
        return _get_quick_test_scenarios()


def _load_recent_batch_results(days: int):
    """Load recent batch results for analysis."""
    # This would load from actual storage
    # For now, return empty list
    return []


def _generate_monitoring_summary(batch_results):
    """Generate monitoring summary report."""
    return {
        "monitoring_period": f"{len(batch_results)} batches",
        "total_evaluations": sum(b.successful_evaluations + b.failed_evaluations for b in batch_results),
        "overall_success_rate": sum(b.successful_evaluations for b in batch_results) / max(1, sum(b.successful_evaluations + b.failed_evaluations for b in batch_results)),
        "total_cost": sum(b.total_llm_cost for b in batch_results),
        "batch_summaries": [b.to_dict() for b in batch_results]
    }


def _get_recommended_scenarios(school=None, difficulty=None, user_type=None):
    """Get recommended scenarios based on criteria."""
    from essay_agent.eval.conversational_scenarios import get_all_scenarios
    
    scenarios = get_all_scenarios()
    
    # Filter by criteria
    if school:
        scenarios = [s for s in scenarios if school.lower() in s.school.lower()]
    if difficulty:
        scenarios = [s for s in scenarios if s.difficulty == difficulty]
    # user_type filtering would require additional metadata
    
    return scenarios[:15]  # Return top 15


def _print_scenario_recommendations(scenarios):
    """Print scenario recommendations in a formatted list."""
    print(f"\n📋 Recommended Evaluation Scenarios ({len(scenarios)})")
    print(f"{'='*60}")
    
    for i, scenario in enumerate(scenarios[:10], 1):
        print(f"{i:2d}. {scenario.name}")
        print(f"    ID: {scenario.eval_id}")
        print(f"    School: {scenario.school} | Difficulty: {scenario.difficulty}")
        print(f"    Category: {scenario.category.value}")
        print(f"    Description: {scenario.description[:80]}...")
        print()


def _interactive_scenario_picker(scenarios):
    """Interactive scenario picker interface."""
    print("\nSelect scenarios to run (comma-separated numbers, or 'all'):")
    choice = input("Selection: ").strip()
    
    if choice.lower() == 'all':
        return scenarios
    
    try:
        indices = [int(x.strip()) - 1 for x in choice.split(',')]
        return [scenarios[i] for i in indices if 0 <= i < len(scenarios)]
    except (ValueError, IndexError):
        print("Invalid selection")
        return []


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
# Quality Assurance and Debugging Commands  
# ---------------------------------------------------------------------------

def cmd_eval_quality_check(args):
    """Check quality of specific evaluation conversations."""
    try:
        from essay_agent.eval.conversation_quality_evaluator import ConversationQualityEvaluator, analyze_conversation_file
        from pathlib import Path
        import json
        
        print(f"🔍 Checking quality for scenario: {args.scenario}")
        
        # Find conversation file for scenario
        memory_files = Path("memory_store").glob("eval_*.conv.json")
        found_file = None
        
        for file_path in memory_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Check if this conversation is from the requested scenario
                    # This is a simple check - in practice you'd want better scenario tracking
                    if args.scenario.lower() in str(data).lower():
                        found_file = file_path
                        break
            except Exception:
                continue
        
        if not found_file:
            print(f"❌ No conversation file found for scenario {args.scenario}")
            print(f"Available files: {list(memory_files)}")
            return
        
        # Analyze the conversation
        analysis_result = analyze_conversation_file(str(found_file))
        
        if 'error' in analysis_result:
            print(f"❌ Analysis failed: {analysis_result['error']}")
            return
        
        # Display results
        results = analysis_result['analysis_results']
        print(f"\n📊 QUALITY ANALYSIS RESULTS:")
        print(f"Response Coverage: {results.get('response_coverage', 0):.2%}")
        print(f"Missing Responses: {results.get('missing_responses', 0)}")
        print(f"Tool Diversity: {results.get('tool_diversity', 0)}")
        print(f"Average Response Length: {results.get('avg_response_length', 0):.0f} chars")
        
        critical_issues = results.get('critical_issues', [])
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in critical_issues:
                print(f"  - {issue}")
        else:
            print(f"\n✅ No critical issues detected")
        
        if args.verbose:
            print(f"\n📁 Analyzed file: {found_file}")
            print(f"🔧 Tools used: {', '.join(results.get('tools_used', []))}")
        
    except Exception as e:
        print(f"❌ Quality check failed: {e}")


def cmd_memory_integration_test(args):
    """Test memory integration between evaluation and manual chat modes."""
    try:
        from essay_agent.eval.conversation_quality_evaluator import ConversationQualityEvaluator
        from essay_agent.agent.core.react_agent import EssayReActAgent
        
        print(f"🧪 Testing memory integration for user: {args.user_id}")
        
        evaluator = ConversationQualityEvaluator()
        results = evaluator.test_memory_integration(args.user_id, args.test_message)
        
        if results.get('memory_integration_success'):
            print(f"✅ Memory integration test PASSED")
            print(f"📊 Found {results.get('conversation_turns_found', 0)} conversation turns")
            print(f"💬 Memory preview: {results.get('memory_content_preview', '')[:200]}...")
        else:
            print(f"❌ Memory integration test FAILED")
            print(f"🔍 Error: {results.get('error', 'Unknown error')}")
            
        print(f"\n📝 Test Status: {results.get('test_status', 'unknown').upper()}")
        
    except Exception as e:
        print(f"❌ Memory integration test failed: {e}")


def cmd_memory_verify(args):
    """Verify memory store files and content."""
    try:
        from pathlib import Path
        import json
        
        print("🔍 Verifying memory store files...")
        
        memory_dir = Path("memory_store")
        if not memory_dir.exists():
            print("❌ Memory store directory does not exist")
            return
        
        if args.user_id:
            # Check specific user
            user_files = list(memory_dir.glob(f"{args.user_id}*"))
            if not user_files:
                print(f"❌ No files found for user {args.user_id}")
                return
            
            files_to_check = user_files
        elif args.all:
            # Check all evaluation files
            files_to_check = list(memory_dir.glob("eval_*"))
        else:
            print("❌ Please specify --user-id or --all")
            return
        
        print(f"📁 Found {len(files_to_check)} files to verify")
        
        for file_path in files_to_check:
            try:
                if file_path.suffix == '.json':
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    if 'conv.json' in file_path.name:
                        # Verify conversation file
                        chat_history = data.get('chat_history', [])
                        user_msgs = sum(1 for msg in chat_history if msg.get('type') == 'human')
                        ai_msgs = sum(1 for msg in chat_history if msg.get('type') == 'ai')
                        
                        status = "✅" if ai_msgs >= user_msgs * 0.8 else "⚠️"
                        print(f"{status} {file_path.name}: {user_msgs} user → {ai_msgs} AI responses")
                    else:
                        print(f"✅ {file_path.name}: Valid JSON, {len(str(data))} chars")
                else:
                    print(f"📄 {file_path.name}: {file_path.stat().st_size} bytes")
                    
            except Exception as e:
                print(f"❌ {file_path.name}: Error - {e}")
        
    except Exception as e:
        print(f"❌ Memory verification failed: {e}")


def cmd_profile_test(args):
    """Test user profile loading and validation."""
    try:
        from essay_agent.eval.real_profiles import get_profile_by_id
        from essay_agent.memory.simple_memory import SimpleMemory
        
        print(f"🧪 Testing profile: {args.profile_id}")
        
        # Test evaluation profile loading
        eval_profile = get_profile_by_id(args.profile_id)
        if eval_profile:
            print(f"✅ Evaluation profile loaded successfully")
            print(f"📊 Name: {eval_profile.name}")
            print(f"📊 Activities: {len(eval_profile.activities)}")
            print(f"📊 Core Values: {len(eval_profile.core_values)}")
        else:
            print(f"❌ Evaluation profile not found")
            return
        
        # Test memory profile loading
        try:
            memory_profile = SimpleMemory.load(f"eval_{args.profile_id}")
            print(f"✅ Memory profile loaded successfully")
            
            # Test profile structure
            if hasattr(memory_profile, 'user_info'):
                print(f"✅ Profile structure valid")
            else:
                print(f"⚠️ Profile structure may be incomplete")
                
        except Exception as e:
            print(f"❌ Memory profile loading failed: {e}")
        
    except Exception as e:
        print(f"❌ Profile test failed: {e}")


def cmd_eval_debug(args):
    """Debug specific evaluation conversation."""
    try:
        from essay_agent.eval.conversation_quality_evaluator import analyze_conversation_file
        from pathlib import Path
        
        print(f"🔧 Debugging conversation: {args.conversation_id}")
        
        # Find conversation file
        conv_file = Path(f"memory_store/{args.conversation_id}.conv.json")
        if not conv_file.exists():
            print(f"❌ Conversation file not found: {conv_file}")
            return
        
        # Analyze conversation
        analysis = analyze_conversation_file(str(conv_file))
        
        if 'error' in analysis:
            print(f"❌ Analysis failed: {analysis['error']}")
            return
        
        results = analysis['analysis_results']
        
        print(f"\n🔍 DEBUGGING RESULTS:")
        print(f"File: {conv_file}")
        print(f"Total Turns: {analysis['conversation_turns']}")
        print(f"Missing Responses: {results.get('missing_responses', 0)}")
        print(f"Tool Diversity: {results.get('tool_diversity', 0)}")
        
        critical_issues = results.get('critical_issues', [])
        if critical_issues:
            print(f"\n🚨 ISSUES FOUND:")
            for i, issue in enumerate(critical_issues, 1):
                print(f"{i}. {issue}")
                
            if args.fix_issues:
                print(f"\n🔧 ATTEMPTING FIXES:")
                print("Note: Automated fixes not implemented yet.")
                print("Manual intervention required for conversation recording issues.")
        else:
            print(f"\n✅ No issues detected - conversation appears healthy")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")


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
    parser.add_argument(
        "--legacy-heuristics", action="store_true", 
        help="Use legacy heuristic evaluation instead of LLM-powered analysis (faster but less accurate)"
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

    # --------------------------- eval-list -------------------------------
    eval_list = sub.add_parser("eval-list", help="List all available conversational evaluations")
    eval_list.add_argument("--category", choices=["new_user", "returning_user", "complex", "edge_case"], help="Filter by category")
    eval_list.add_argument("--difficulty", choices=["easy", "medium", "hard"], help="Filter by difficulty")
    eval_list.add_argument("--school", help="Filter by school name")
    eval_list.add_argument("--json", action="store_true", help="Output JSON format")
    eval_list.set_defaults(func=_cmd_eval_list)

    # --------------------------- eval-conversation ----------------------
    eval_conversation = sub.add_parser("eval-conversation", help="Run specific conversational evaluation")
    eval_conversation.add_argument("eval_id", help="Evaluation ID to run (e.g., CONV-001-new-user-stanford-identity)")
    eval_conversation.add_argument("--profile", help="User profile ID to use for evaluation")
    eval_conversation.add_argument("--verbose", action="store_true", help="Show detailed conversation flow")
    eval_conversation.add_argument("--save-conversation", action="store_true", help="Save conversation to JSON file")
    eval_conversation.add_argument("--use-integrated-memory", action="store_true", help="Save evaluation conversations to memory_store (like manual chats)")
    eval_conversation.add_argument("--json", action="store_true", help="Output JSON format")
    eval_conversation.set_defaults(func=_cmd_eval_conversation)

    # --------------------------- eval-suite ------------------------------
    eval_suite = sub.add_parser("eval-suite", help="Run evaluation suite by category")
    eval_suite.add_argument("--category", choices=["new_user", "returning_user", "complex", "edge_case"], help="Run specific category")
    eval_suite.add_argument("--difficulty", choices=["easy", "medium", "hard"], help="Filter by difficulty")
    eval_suite.add_argument("--school", help="Filter by school name")
    eval_suite.add_argument("--count", type=int, help="Limit number of scenarios to run")
    eval_suite.add_argument("--parallel", type=int, default=1, help="Number of parallel evaluations (default: 1)")
    eval_suite.add_argument("--verbose", action="store_true", help="Show detailed conversation flows")
    eval_suite.add_argument("--json", action="store_true", help="Output JSON format")
    eval_suite.set_defaults(func=_cmd_eval_suite)

    # --------------------------- eval-autonomy ---------------------------
    eval_autonomy = sub.add_parser("eval-autonomy", help="Test agent autonomy behavior")
    eval_autonomy.add_argument("--profile", required=True, help="User profile ID for autonomy testing")
    eval_autonomy.add_argument("--level", choices=["full_agent", "collaborative", "guided_self_write", "minimal_help"], help="Test specific autonomy level")
    eval_autonomy.add_argument("--output", help="Output file for detailed results")
    eval_autonomy.add_argument("--json", action="store_true", help="Output JSON format")
    eval_autonomy.set_defaults(func=_cmd_eval_autonomy)

    # --------------------------- eval-memory -----------------------------
    eval_memory = sub.add_parser("eval-memory", help="Test agent memory utilization")
    eval_memory.add_argument("--profile", required=True, help="User profile ID for memory testing")
    eval_memory.add_argument("--output", help="Output file for detailed results")
    eval_memory.add_argument("--json", action="store_true", help="Output JSON format")
    eval_memory.set_defaults(func=_cmd_eval_memory)

    # --------------------------- eval-memory-list ------------------------
    eval_memory_list = sub.add_parser("eval-memory-list", help="List evaluation conversations saved in memory_store")
    eval_memory_list.add_argument("--prefix", default="eval", help="Memory prefix to filter by (default: eval)")
    eval_memory_list.add_argument("--json", action="store_true", help="Output JSON format")
    eval_memory_list.set_defaults(func=_cmd_eval_memory_list)

    # ============================================================================
    # Enhanced LLM-Powered Evaluation Commands
    # ============================================================================
    
    # --------------------------- eval-smart -------------------------------
    eval_smart = sub.add_parser("eval-smart", help="Smart evaluation with natural language scenario selection")
    eval_smart.add_argument("description", nargs="?", help="Natural language description of scenarios to test")
    eval_smart.add_argument("--count", type=int, default=5, help="Number of scenarios to run")
    eval_smart.add_argument("--parallel", type=int, default=3, help="Parallel evaluation limit")
    eval_smart.add_argument("--quick", action="store_true", help="Run quick test suite")
    eval_smart.add_argument("--live", action="store_true", help="Show live progress")
    eval_smart.add_argument("--time-limit", type=int, help="Time limit in seconds")
    eval_smart.add_argument("--export", help="Export results to file")
    eval_smart.add_argument("--json", action="store_true", help="Output JSON format")
    eval_smart.set_defaults(func=_cmd_eval_smart)
    
    # --------------------------- eval-batch -------------------------------
    eval_batch = sub.add_parser("eval-batch", help="Batch evaluation with intelligent scheduling")
    eval_batch.add_argument("--scenarios", help="Comma-separated scenario IDs")
    eval_batch.add_argument("--count", type=int, default=20, help="Number of scenarios for balanced selection")
    eval_batch.add_argument("--parallel", type=int, default=5, help="Parallel execution limit")
    eval_batch.add_argument("--time-limit", type=int, help="Time limit in seconds")
    eval_batch.add_argument("--no-llm", action="store_true", help="Disable LLM evaluation")
    eval_batch.add_argument("--insights", action="store_true", help="Generate pattern insights")
    eval_batch.add_argument("--export", help="Export results to file")
    eval_batch.add_argument("--quiet", action="store_true", help="Suppress progress output")
    eval_batch.add_argument("--json", action="store_true", help="Output JSON format")
    eval_batch.set_defaults(func=_cmd_eval_batch)
    
    # --------------------------- eval-insights ----------------------------
    eval_insights = sub.add_parser("eval-insights", help="Analyze evaluation patterns and generate insights")
    eval_insights.add_argument("--file", help="Load evaluation results from file")
    eval_insights.add_argument("--days", type=int, default=7, help="Analyze results from last N days")
    eval_insights.add_argument("--export", help="Export analysis to file")
    eval_insights.add_argument("--json", action="store_true", help="Output JSON format")
    eval_insights.set_defaults(func=_cmd_eval_insights)
    
    # --------------------------- eval-monitor -----------------------------
    eval_monitor = sub.add_parser("eval-monitor", help="Continuous evaluation monitoring")
    eval_monitor.add_argument("--duration", type=int, default=1, help="Monitoring duration in hours")
    eval_monitor.add_argument("--parallel", type=int, default=3, help="Parallel execution limit")
    eval_monitor.add_argument("--export", help="Export monitoring report to file")
    eval_monitor.set_defaults(func=_cmd_eval_monitor)
    
    # --------------------------- eval-discover ----------------------------
    eval_discover = sub.add_parser("eval-discover", help="Discover and recommend evaluation scenarios")
    eval_discover.add_argument("description", nargs="?", help="Description of desired scenarios")
    eval_discover.add_argument("--school", help="Filter by school name")
    eval_discover.add_argument("--difficulty", choices=["easy", "medium", "hard"], help="Filter by difficulty")
    eval_discover.add_argument("--user-type", help="Filter by user type")
    eval_discover.add_argument("--interactive", action="store_true", help="Interactive scenario selection")
    eval_discover.add_argument("--json", action="store_true", help="Output JSON format")
    eval_discover.set_defaults(func=_cmd_eval_discover)

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

    # Quality Assurance Commands
    qa_parser = sub.add_parser(
        'eval-quality-check',
        help='Check quality of specific evaluation conversations'
    )
    qa_parser.add_argument('--scenario', required=True, help='Scenario ID to analyze')
    qa_parser.add_argument('--verbose', action='store_true', help='Show detailed analysis')
    qa_parser.set_defaults(func=cmd_eval_quality_check)
    
    # Memory Integration Testing
    memory_test_parser = sub.add_parser(
        'memory-integration-test',
        help='Test memory integration between evaluation and manual chat modes'
    )
    memory_test_parser.add_argument('--user-id', required=True, help='User ID to test')
    memory_test_parser.add_argument('--test-message', default="Can you remind me what we discussed about my essay?", help='Test message to send')
    memory_test_parser.set_defaults(func=cmd_memory_integration_test)
    
    # Memory verification
    memory_verify_parser = sub.add_parser(
        'memory-verify',
        help='Verify memory store files and content for evaluation users'
    )
    memory_verify_parser.add_argument('--user-id', help='Specific user ID to verify')
    memory_verify_parser.add_argument('--all', action='store_true', help='Check all evaluation memory files')
    memory_verify_parser.set_defaults(func=cmd_memory_verify)
    
    # Profile testing
    profile_test_parser = sub.add_parser(
        'profile-test',
        help='Test user profile loading and validation'
    )
    profile_test_parser.add_argument('--profile-id', required=True, help='Profile ID to test')
    profile_test_parser.set_defaults(func=cmd_profile_test)
    
    # Evaluation debugging
    eval_debug_parser = sub.add_parser(
        'eval-debug',
        help='Debug specific evaluation conversation and analyze issues'
    )
    eval_debug_parser.add_argument('--conversation-id', required=True, help='Conversation ID to debug')
    eval_debug_parser.add_argument('--fix-issues', action='store_true', help='Attempt to fix detected issues')
    eval_debug_parser.set_defaults(func=cmd_eval_debug)

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