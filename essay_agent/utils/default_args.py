from __future__ import annotations

"""essay_agent.utils.default_args

Argument autofill helper used by SmartOrchestrator (U4-02).
Fills missing tool parameters from current context and memory.
"""
from typing import Any, Dict, Callable, List
import inspect

# Registry import required for catch-all injection
from essay_agent.tools import REGISTRY


# ---------------------------------------------------------------------------
# Rule registry – map tool_name -> callable
# ---------------------------------------------------------------------------

AUTOFILL_RULES: Dict[str, Callable[[Dict[str, Any], Dict[str, Any], Any], Dict[str, Any]]] = {}

# ============================================================================
# Rule definitions
# ============================================================================

# This function is being removed as its logic is flawed and is being replaced
# by a more robust, inspection-based approach in the main autofill_args function.

# ------------------------------------------------------------------
# Helper rule definitions ------------------------------------------
# ------------------------------------------------------------------


def _safe_get_recent_chat(ctx: Dict[str, Any]) -> str:  # noqa: D401
    """Return last user chat line if available else empty string."""
    recent = ctx.get("recent_chat") or ctx.get("recent_messages") or []
    if isinstance(recent, list) and recent:
        return recent[-1]
    return ""


def _rule_clarify(args: Dict[str, Any], ctx: Dict[str, Any], mem):
    """Ensure clarify tool receives the triggering user_input."""
    args.setdefault("user_input", _safe_get_recent_chat(ctx))
    return args


def _rule_outline_generator(args: Dict[str, Any], ctx: Dict[str, Any], mem):
    """Fill story + essay_prompt for outline_generator."""
    # Allow alias 'story_idea' and fallbacks from context
    story = (
        args.pop("story_idea", None)
        or args.get("story")
        or ctx.get("story")
        or ctx.get("brainstorm_specific", {}).get("best_idea")
        or ctx.get("brainstorm", {}).get("ideas", [{}])[0]
    )
    if story:
        args["story"] = story

    # Always include essay_prompt from memory
    args.setdefault("essay_prompt", mem.get("essay_prompt", ""))
    return args


def _rule_length_optimizer(args: Dict[str, Any], ctx: Dict[str, Any], mem):
    """Ensure outline + target_word_count present."""
    if "outline" not in args or not args["outline"]:
        args["outline"] = ctx.get("outline") or ctx.get("outline_generator", {}).get("outline", {})
    args.setdefault("target_word_count", getattr(mem, "preferences", {}).get("preferred_word_count", 650))
    return args


def _rule_suggest_stories(args: Dict[str, Any], ctx: Dict[str, Any], mem):
    args.setdefault("essay_prompt", mem.get("essay_prompt", ""))
    # Ensure profile present (raw dict)
    args.setdefault("profile", mem.user_profile.model_dump() if hasattr(mem, "user_profile") else {})
    # Inject triggering user input (U4-02-E)
    args.setdefault("user_input", _safe_get_recent_chat(ctx))
    return args


def _rule_story_development(args: Dict[str, Any], ctx: Dict[str, Any], mem):
    args.setdefault("story", ctx.get("story") or ctx.get("suggest_stories", {}).get("stories", [{}])[0].get("description", ""))
    args.setdefault("user_input", _safe_get_recent_chat(ctx))
    return args


def _rule_story_themes(args: Dict[str, Any], ctx: Dict[str, Any], mem):
    args.setdefault("story", ctx.get("story") or ctx.get("story_development", {}).get("developed_story", ""))
    return args


def _rule_validate_uniqueness(args: Dict[str, Any], ctx: Dict[str, Any], mem):
    args.setdefault("story_angle", ctx.get("story") or ctx.get("story_development", {}).get("developed_story", ""))
    return args


def _rule_brainstorm_specific(args: Dict[str, Any], ctx: Dict[str, Any], mem, user_input: str):
    """Fills the 'topic' argument from the user's input."""
    # A simple heuristic: assume the user's input *is* the topic.
    # More advanced logic could use NLP to extract it.
    if "topic" not in args or not args["topic"]:
        args["topic"] = user_input
    return args


# ------------------------------------------------------------------
# U4-02-D – expand_outline_section autofill -------------------------
# ------------------------------------------------------------------


def _rule_expand_outline_section(args: Dict[str, Any], ctx: Dict[str, Any], mem):
    """Derive outline_section, section_name, voice_profile."""

    outline_obj = ctx.get("outline") or ctx.get("outline_generator", {}).get("outline", {})

    # Resolve section
    section = args.get("section") or args.get("section_name") or "hook"
    args.setdefault("section_name", section)

    # Inject outline text for that section if available
    if outline_obj and isinstance(outline_obj, dict):
        args.setdefault("outline_section", outline_obj.get(section, ""))

    # User voice
    args.setdefault("voice_profile", getattr(mem, "preferences", {}).get("tone", ""))
    return args


def _rule_outline(args: Dict[str, Any], ctx: Dict[str, Any], mem):  # noqa: D401
    latest_brainstorm = ctx.get("brainstorm_specific", {}) if isinstance(ctx.get("brainstorm_specific"), dict) else {}
    args.setdefault("story", latest_brainstorm.get("best_idea", ""))
    args.setdefault("prompt", mem.get("essay_prompt", ""))
    args.setdefault("word_count", getattr(mem, "preferences", {}).get("preferred_word_count", 650))
    return args


def _rule_draft(args: Dict[str, Any], ctx: Dict[str, Any], mem):  # noqa: D401
    args.setdefault("outline", ctx.get("outline", {}))
    args.setdefault("voice_profile", getattr(mem, "preferences", {}).get("tone", ""))
    args.setdefault("word_count", getattr(mem, "preferences", {}).get("preferred_word_count", 650))
    return args


def _rule_word_count(args: Dict[str, Any], ctx: Dict[str, Any], mem):  # noqa: D401
    # Count words of latest draft if text missing
    if "text" not in args or not args["text"]:
        draft_obj = ctx.get("draft", {})
        text = draft_obj.get("draft") if isinstance(draft_obj, dict) else ""
        args["text"] = text
    return args


# Register core rules --------------------------------------------------------
for _name, _fn in {
    "outline": _rule_outline,
    "draft": _rule_draft,
    "word_count": _rule_word_count,
    "clarify": _rule_clarify,
    "outline_generator": _rule_outline_generator,
    "length_optimizer": _rule_length_optimizer,
    "suggest_stories": _rule_suggest_stories,
    "story_development": _rule_story_development,
    "story_themes": _rule_story_themes,
    "validate_uniqueness": _rule_validate_uniqueness,
    "expand_outline_section": _rule_expand_outline_section,
    "brainstorm_specific": _rule_brainstorm_specific,
}.items():
    AUTOFILL_RULES[_name] = _fn


# ============================================================================
# Main autofill function
# ============================================================================

def autofill_args(step: Dict[str, Any], context: Dict[str, Any], memory: Any, user_input: str) -> Dict[str, Any]:
    """Autofill missing arguments for a plan step based on context and memory.
    
    This function applies a two-pass process:
    1. A general, inspection-based rule that provides the user_input to any
       common text-based parameter that is required by the tool but was not
       provided by the planner.
    2. A specific, tool-by-tool rule that can apply more complex logic to
       derive arguments from memory or context, overriding the general rule
       if necessary.
        
    Args:
        step: A dictionary representing a single step in a plan.
        context: The current context snapshot.
        memory: The agent's memory instance.
        user_input: The raw user input for the current turn.
        
    Returns:
        The step's arguments, with missing values filled in.
    """
    tool_name = step.get("tool") or step.get("tool_name")
    args = step.get("args", {}).copy() # Use a copy to avoid side-effects

    # 1. General rule: Inject user_input for missing required text arguments
    tool_instance = REGISTRY.get(tool_name)
    if tool_instance:
        # Determine the actual callable for the tool
        if hasattr(tool_instance, "run") and callable(tool_instance.run):
            func = tool_instance.run
        elif callable(tool_instance):
            func = tool_instance
        else:
            func = None
        
        if func:
            sig = inspect.signature(func)
            required_args = {
                p.name
                for p in sig.parameters.values()
                if p.default == inspect.Parameter.empty and p.name not in ('self', 'kwargs', 'args')
            }
            
            # Common names for a text-like argument that can be satisfied by the user's raw input
            TEXT_LIKE_ARGS = {"text", "story", "selection", "user_input", "essay_prompt", "prompt", "tool_input", "topic"}

            missing_required_args = required_args - set(args.keys())
            
            # Intelligently find the single, most likely text-based argument to fill.
            text_arg_to_fill = next((arg for arg in missing_required_args if arg in TEXT_LIKE_ARGS), None)

            if text_arg_to_fill:
                args[text_arg_to_fill] = user_input

    # 2. Specific rules: Apply registered rule for the tool, which can override the general fill.
    if tool_name in AUTOFILL_RULES:
        rule = AUTOFILL_RULES[tool_name]
        sig = inspect.signature(rule)
        # Pass user_input only if the specific rule is designed to accept it
        if "user_input" in sig.parameters:
            args = rule(args, context, memory, user_input)
        else:
            args = rule(args, context, memory)
            
    return args 