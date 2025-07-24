from __future__ import annotations

"""essay_agent.utils.arg_resolver

Generic argument resolver that inspects TOOL_ARG_SPEC and fills in all
required arguments for a tool from (1) planner-provided args, (2) context
snapshot, (3) user profile memory, (4) user’s last input, and (5) sensible
default fallbacks.  Designed for Phase-6 automatic parameter mapping.
"""

import os
from typing import Any, Dict, List

# Avoid circular import by lazy-importing tool metadata inside resolve

__all__ = ["MissingRequiredArgError", "ArgResolver"]


class MissingRequiredArgError(RuntimeError):
    """Raised when ArgResolver cannot supply a required parameter."""


class ArgResolver:
    """Resolve missing kwargs for a tool using layered sources.

    Usage
    -----
    >>> resolver = ArgResolver()
    >>> kwargs = resolver.resolve(
    ...     tool_name="brainstorm",
    ...     planner_args={"prompt": "..."},
    ...     context=context_snapshot,
    ...     user_input="Help me brainstorm …",
    ... )
    """

    # Cheap per-process cache -------------------------------------------------
    _CACHE: Dict[str, List[str]] = {}

    # Very small set of generic defaults – extended as needed
    _DEFAULTS: Dict[str, Any] = {
        "word_limit": 650,
        "tone": "neutral",
    }

    # Common aliases – key : list[alternative_keys]
    _ALIASES: Dict[str, List[str]] = {
        "essay_prompt": ["prompt", "question"],
        "profile": ["user_profile", "student_profile"],
        "selection": ["text", "snippet"],
    }

    def resolve(
        self,
        tool_name: str,
        *,
        planner_args: Dict[str, Any] | None = None,
        context: Dict[str, Any] | None = None,
        user_input: str = "",
        verbose: bool | None = None,
    ) -> Dict[str, Any]:
        """Return kwargs dict for *tool_name* or raise MissingRequiredArgError."""
        planner_args = planner_args or {}
        context = context or {}
        verbose = verbose if verbose is not None else os.getenv("ESSAY_AGENT_SHOW_ARGS") == "1"

        # Lazy import to avoid circular dependency
        from essay_agent.tools import TOOL_ARG_SPEC, get_required_args, get_optional_args

        required = get_required_args(tool_name)
        optional = get_optional_args(tool_name)
        all_params = set(required + optional)

        resolved: Dict[str, Any] = {}
        diagnostics: Dict[str, str] = {}

        # Helper that writes then records source
        def _set(key: str, value: Any, source: str):
            if key not in resolved and value is not None:
                resolved[key] = value
                diagnostics[key] = source

        # 1) Planner args ---------------------------------------------------
        for k, v in planner_args.items():
            _set(k, v, "planner")

        # 2) Flattened context ---------------------------------------------
        flat_ctx: Dict[str, Any] = {}

        def _flatten(prefix: str, obj: Any):
            if isinstance(obj, dict):
                for kk, vv in obj.items():
                    new_prefix = f"{prefix}_{kk}" if prefix else kk
                    flat_ctx[new_prefix] = vv
                    _flatten(new_prefix, vv)

        _flatten("", context)

        # Memory-based fallback (common for college_id and college)
        if "college_id" in all_params and "college_id" not in resolved:
            mem_college = context.get("college") or context.get("college_context", {}).get("school") or context.get("profile", {}).get("college")
            if mem_college:
                _set("college_id", mem_college, "memory")
        
        # Enhanced college context resolution 
        if "college" in all_params and "college" not in resolved:
            college_value = (
                context.get("college") or 
                context.get("college_context", {}).get("school") or
                flat_ctx.get("college") or
                flat_ctx.get("college_context_school")
            )
            if college_value:
                _set("college", college_value, "context")
            else:
                _set("college", "this college", "default")

        # Default profile fallback to avoid tool failure
        if "profile" in all_params and "profile" not in resolved:
            # Try multiple context keys for user profile data
            ctx_profile = (
                context.get("profile") or 
                context.get("user_profile") or
                flat_ctx.get("user_profile")
            )
            
            if ctx_profile:
                # Format rich profile data for tool consumption
                if isinstance(ctx_profile, dict):
                    formatted_profile = self._format_profile_for_tools(ctx_profile)
                    _set("profile", formatted_profile, "context")
                else:
                    _set("profile", str(ctx_profile), "context")
            else:
                _set("profile", "New applicant; profile pending.", "default")
        for k in all_params:
            if k in context:
                _set(k, context[k], "context")
            elif k in flat_ctx:
                _set(k, flat_ctx[k], "context_flat")

        # 3) User input heuristics (simple) ---------------------------------
        if user_input and "selection" in all_params and "selection" not in resolved:
            _set("selection", user_input, "user_input")
        
        # Map user_input for tools that need it (like clarify)
        if user_input and "user_input" in all_params and "user_input" not in resolved:
            _set("user_input", user_input, "user_input")
        
        # Enhanced essay_prompt resolution
        if "essay_prompt" in all_params and "essay_prompt" not in resolved:
            essay_prompt_value = (
                context.get("essay_prompt") or
                context.get("college_context", {}).get("essay_prompt") or
                flat_ctx.get("essay_prompt") or
                flat_ctx.get("college_context_essay_prompt")
            )
            if essay_prompt_value:
                _set("essay_prompt", essay_prompt_value, "context")

        # 4) Defaults -------------------------------------------------------
        for k in all_params:
            if k not in resolved and k in self._DEFAULTS:
                _set(k, self._DEFAULTS[k], "default")

        # 5) Alias lookup ---------------------------------------------------
        missing_after_defaults = [k for k in required if k not in resolved]
        for missing_key in missing_after_defaults:
            for alias in self._ALIASES.get(missing_key, []):
                # Planner args first
                if alias in planner_args:
                    _set(missing_key, planner_args[alias], f"alias:{alias}")
                    break
                # Context flat search
                if alias in context:
                    _set(missing_key, context[alias], f"alias:{alias}")
                    break
                if alias in flat_ctx:
                    _set(missing_key, flat_ctx[alias], f"alias:{alias}")
                    break

        # Fail if any required missing -------------------------------------
        missing = [k for k in required if k not in resolved]
        if missing:
            raise MissingRequiredArgError(
                f"Missing required args for {tool_name}: {', '.join(missing)}"
            )

        if verbose:
            from pprint import pformat

            print("\n--- ARG RESOLVER (tool=" + tool_name + ") ---")
            print(pformat({"resolved": resolved, "sources": diagnostics}))

        return resolved 

    def _format_profile_for_tools(self, profile_dict: Dict[str, Any]) -> str:
        """Format rich user profile data into a concise string for tool consumption.
        
        Args:
            profile_dict: Full user profile dictionary
            
        Returns:
            Formatted profile string with key details for brainstorming
        """
        try:
            # Extract key profile sections
            user_info = profile_dict.get("user_info", {})
            activities = profile_dict.get("academic_profile", {}).get("activities", [])
            defining_moments = profile_dict.get("defining_moments", [])
            core_values = profile_dict.get("core_values", [])
            
            # Build formatted profile string
            parts = []
            
            # Basic info
            name = user_info.get("name", "Student")
            major = user_info.get("intended_major", "")
            if major:
                parts.append(f"{name}: {major}-focused student")
            else:
                parts.append(name)
            
            # Key activities (top 3)
            if activities:
                activity_summaries = []
                for activity in activities[:3]:
                    role = activity.get("role", "")
                    name_act = activity.get("name", "")
                    impact = activity.get("impact", "")
                    if role and name_act:
                        if impact:
                            activity_summaries.append(f"{role} of {name_act} ({impact[:50]}...)")
                        else:
                            activity_summaries.append(f"{role} of {name_act}")
                
                if activity_summaries:
                    parts.append(f"Activities: {', '.join(activity_summaries)}")
            
            # Defining moments with relevant themes
            if defining_moments:
                moment_themes = []
                for moment in defining_moments[:3]:
                    title = moment.get("title", "")
                    themes = moment.get("themes", [])
                    if title and themes:
                        moment_themes.append(f"{title} (themes: {', '.join(themes[:2])})")
                
                if moment_themes:
                    parts.append(f"Key experiences: {'; '.join(moment_themes)}")
            
            # Core values (top 2)
            if core_values:
                value_names = [v.get("value", "") for v in core_values[:2] if v.get("value")]
                if value_names:
                    parts.append(f"Core values: {', '.join(value_names)}")
            
            return ". ".join(parts) + "."
            
        except Exception as e:
            # Fallback to basic string representation
            return f"Student profile: {str(profile_dict)[:200]}..." 