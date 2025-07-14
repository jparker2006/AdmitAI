"""
EssayPlanner - 100x Project Planner Skeleton

High-level responsibilities:
1. Interpret user input & memory state
2. Decide next action in the essay workflow
3. Return structured plan objects for the executor

TODO:
- Implement enum `Phase` for writing stages
- Add method `decide_next_action`
- Interface with memory (to be defined in memory module)
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Any, Optional, Tuple, Mapping
import json, os
from essay_agent.prompts import SYSTEM_PROMPT, PLANNER_REACT_PROMPT
from essay_agent.prompts.smart_planning import SMART_PLANNING_PROMPT
from essay_agent.tools import REGISTRY as TOOL_REGISTRY

# Memory system imports
from essay_agent.memory import HierarchicalMemory, SimpleMemory
from essay_agent.memory.simple_memory import is_story_reused

# LangChain imports ---------------------------------------------------------
# Prefer langchain_openai (recommended) then community path, fallback to legacy
try:
    from langchain_openai import ChatOpenAI  # type: ignore
except ImportError:  # pragma: no cover – use community or legacy
    try:
        from langchain_community.chat_models import ChatOpenAI  # type: ignore
    except ImportError:  # pragma: no cover
        try:
            from langchain.chat_models import ChatOpenAI  # type: ignore
        except ImportError:
            ChatOpenAI = None  # type: ignore

# FakeListLLM remains the same for offline tests
try:
    from langchain.llms.fake import FakeListLLM  # type: ignore
except ImportError:
    FakeListLLM = None  # type: ignore


class Phase(Enum):
    """Writing phases for essay workflow."""

    BRAINSTORMING = auto()
    OUTLINING = auto()
    DRAFTING = auto()
    REVISING = auto()
    POLISHING = auto()


@dataclass
class Plan:
    """Container describing executor actions."""

    phase: Phase
    tasks: List[str]
    metadata: Dict[str, Any]


# ---------------------------------------------------------------------------
# LangGraph-compatible plan structure
# ---------------------------------------------------------------------------


@dataclass
class EssayPlan:
    """State container that flows through the LangGraph executor."""

    phase: Phase = Phase.BRAINSTORMING
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Update return type for MVP while keeping backward compatibility ------------


class EssayPlanner:
    """Stateless planner (will reference memory in later iterations)."""

    def decide_next_action(self, user_input: str, context: Dict[str, Any]) -> EssayPlan:  # type: ignore[override]
        """Placeholder decision engine.

        Args:
            user_input: Raw user message.
            context: Dict containing memory snapshot & conversation state.
        Returns:
            EssayPlan: structured description of tasks for Executor.
        """

        # Lazy-init ReAct planner --------------------------------------------------
        if not hasattr(self, "_react"):
            self._react = EssayReActPlanner()

        return self._react.decide_next_action(user_input, context)


# ---------------------------------------------------------------------------
# ReAct planner implementation
# ---------------------------------------------------------------------------


class EssayReActPlanner:
    """LLM-driven planner that selects the next tool using intelligent analysis."""

    def __init__(self, llm=None):
        if llm is None:
            # Always default to deterministic FakeListLLM when no explicit LLM
            # is supplied.  This guarantees offline/CI stability regardless of
            # OPENAI_API_KEY presence.
            responses = [
                '{"tool": "brainstorm", "args": {}, "reasoning": {"decision_type": "CONTINUE"}, "metadata": {"phase": "BRAINSTORMING"}}'
            ]
            llm = FakeListLLM(responses=responses) if FakeListLLM else None

        self.llm = llm

        # Build prompt content ------------------------------------------------
        self._tool_list_str = "\n".join(f"- {name}" for name in TOOL_REGISTRY.keys())

    # ------------------------------------------------------------------
    def decide_next_action(self, user_input: str, context: Dict[str, Any]) -> EssayPlan:  # noqa: D401
        """Enhanced intelligent planner with context analysis and quality evaluation."""
        # ------------------------------------------------------------------
        # QUICK RULE-BASED ARG BUILDER (MVP) --------------------------------
        # Until the full LLM planning logic is battle-tested we employ a
        # deterministic mapping that *also* populates `args` so downstream
        # tools receive the inputs they require.  When the smart-planner is
        # enabled this block will be skipped because the LLM will already
        # provide `args` in its JSON response.
        # ------------------------------------------------------------------

        outputs_now = context.get("tool_outputs", {}) or {}
        sequence = ["brainstorm", "outline", "draft", "revise", "polish"]
        next_tool = next((t for t in sequence if t not in outputs_now), "finish_workflow")

        # Helper to build minimal args --------------------------------------
        def _guess_args(tool: str, user_input: str, ctx: Mapping[str, Any]):
            outputs = ctx.get("tool_outputs", {}) or {}
            user_profile_raw = ctx.get("user_profile", {})
            # Handle datetime serialization safely
            try:
                user_profile_str = json.dumps(user_profile_raw, ensure_ascii=False, default=str) if user_profile_raw else ""
            except Exception:
                user_profile_str = str(user_profile_raw) if user_profile_raw else ""

            # Helper to extract successful result from tool output
            def extract_result(tool_output):
                if isinstance(tool_output, dict):
                    if "error" in tool_output and tool_output["error"] is not None:
                        return None  # Tool failed
                    if "ok" in tool_output:
                        return tool_output["ok"]
                return tool_output

            if tool == "brainstorm":
                args = {"essay_prompt": user_input, "profile": user_profile_str}
            elif tool == "outline":
                brainstorm_result = extract_result(outputs.get("brainstorm"))
                if brainstorm_result and isinstance(brainstorm_result, dict) and "stories" in brainstorm_result:
                    stories = brainstorm_result["stories"]
                    story_title = stories[0].get("title", "Personal Story") if stories else "Personal Story"
                else:
                    story_title = "Personal Story"
                args = {"story": story_title, "prompt": user_input, "word_count": ctx.get("word_limit", 650)}
            elif tool == "draft":
                outline_result = extract_result(outputs.get("outline"))
                brainstorm_result = extract_result(outputs.get("brainstorm"))
                
                if outline_result is None:
                    # Use fallback outline
                    outline_result = {
                        "outline": {
                            "hook": "Opening sentence",
                            "context": "Background information",
                            "conflict": "Challenge or obstacle",
                            "growth": "Learning and development",
                            "reflection": "Insights and conclusion"
                        }
                    }
                
                # Extract selected story information from brainstorm
                selected_story = None
                if brainstorm_result and isinstance(brainstorm_result, dict) and "stories" in brainstorm_result:
                    stories = brainstorm_result["stories"]
                    if stories:
                        selected_story = stories[0]  # First story is the selected one
                
                # Create focused voice profile with selected story
                voice_profile_focused = user_profile_str or "Neutral, authentic first-person voice"
                if selected_story:
                    # Create a focused context that highlights the selected story
                    import json
                    try:
                        profile_data = json.loads(user_profile_str) if user_profile_str else {}
                        focused_profile = {
                            "selected_story": selected_story,
                            "user_info": profile_data.get("user_info", {}),
                            "core_values": profile_data.get("core_values", []),
                            "writing_voice": profile_data.get("writing_voice"),
                            "essay_history": profile_data.get("essay_history", [])[-3:]  # Only recent essays for context
                        }
                        voice_profile_focused = json.dumps(focused_profile, indent=2, default=str)
                    except (json.JSONDecodeError, KeyError):
                        pass  # Fall back to original voice profile
                
                args = {
                    "outline": outline_result,
                    "voice_profile": voice_profile_focused,
                    "word_count": ctx.get("word_limit", 650),
                }
            elif tool == "revise":
                draft_result = extract_result(outputs.get("draft"))
                if draft_result is None:
                    # If draft failed, skip revision and go to polish
                    return {}

                # If the draft_result is a mapping like {"draft": "..."} extract the raw string
                if isinstance(draft_result, dict):
                    draft_result = draft_result.get("draft") or draft_result.get("revised_draft") or ""

                if not isinstance(draft_result, str) or not draft_result.strip():
                    # Invalid draft – fallback to polish directly
                    return {}

                args = {
                    "draft": draft_result,
                    "revision_focus": "clarity and flow",
                }
            elif tool == "polish":
                revise_result = extract_result(outputs.get("revise"))
                if revise_result is None:
                    # Fall back to draft if revision failed
                    draft_result = extract_result(outputs.get("draft"))
                    if draft_result is None:
                        raise ValueError("Cannot polish - no draft available")
                    if isinstance(draft_result, dict):
                        draft_result = draft_result.get("revised_draft") or draft_result.get("draft") or ""
                    args = {"draft": draft_result, "word_count": ctx.get("word_limit", 650)}
                else:
                    if isinstance(revise_result, dict):
                        revise_result = revise_result.get("revised_draft") or revise_result.get("draft") or ""
                    args = {"draft": revise_result, "word_count": ctx.get("word_limit", 650)}
            else:
                args = {}
            
            return args

        # ---- MVP deterministic path --------------------------------------
        args_built = _guess_args(next_tool, user_input, context)
        return EssayPlan(phase=_phase_from_tool(next_tool), data={"next_tool": next_tool, "args": args_built})

    def _analyze_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze context to extract memory state, tool outputs, and conversation history."""
        
        analysis = {
            "user_profile": "{}",
            "essay_history": "[]", 
            "conversation_context": "[]",
            "working_memory": "[]",
            "tool_outputs": "{}"
        }
        
        try:
            # Extract user ID and load memory if available
            user_id = context.get("user_id")
            if user_id:
                try:
                    # Load hierarchical memory
                    memory = HierarchicalMemory(user_id)
                    
                    # Extract user profile
                    analysis["user_profile"] = json.dumps(memory.profile.model_dump(), indent=2)
                    
                    # Extract essay history
                    essay_history = [record.model_dump() for record in memory.profile.essay_history]
                    analysis["essay_history"] = json.dumps(essay_history, indent=2)
                    
                    # Extract conversation context
                    recent_chat = memory.get_recent_chat(k=10)
                    analysis["conversation_context"] = json.dumps(recent_chat, indent=2)
                    
                    # Extract working memory
                    working_memory_data = {
                        "core_values": [cv.model_dump() for cv in memory.profile.core_values],
                        "defining_moments": [dm.model_dump() for dm in memory.profile.defining_moments]
                    }
                    analysis["working_memory"] = json.dumps(working_memory_data, indent=2)
                    
                except Exception:
                    # If memory loading fails, use simple memory fallback
                    profile = SimpleMemory.load(user_id)
                    analysis["user_profile"] = json.dumps(profile.model_dump(), indent=2)
            
            # Extract tool outputs from context
            tool_outputs = context.get("tool_outputs", {})
            if tool_outputs:
                analysis["tool_outputs"] = json.dumps(tool_outputs, indent=2)
            
            # Extract conversation history from context
            conversation_history = context.get("conversation_history", [])
            if conversation_history:
                analysis["conversation_context"] = json.dumps(conversation_history, indent=2)
            
        except Exception:
            # If context analysis fails, use empty defaults
            pass
        
        return analysis

    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from LLM response that may contain reasoning text."""
        
        # Look for JSON block in response
        response = response.strip()
        
        # Try to find JSON block markers
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end != -1:
                return response[start:end].strip()
        
        # Try to find raw JSON (starts with { and ends with })
        start = response.find("{")
        if start != -1:
            # Find the matching closing brace
            brace_count = 0
            end = start
            for i, char in enumerate(response[start:], start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            return response[start:end]
        
        # If no JSON found, return the whole response and let JSON parsing fail
        return response

    def _fallback_simple_planning(self, user_input: str, context: Dict[str, Any], 
                                 raw_response: str, error: str) -> EssayPlan:
        """Fallback to simple planning when smart planning fails."""
        
        try:
            # Use legacy simple planning logic
            prompt = PLANNER_REACT_PROMPT.format(
                system=SYSTEM_PROMPT, 
                tools=self._tool_list_str, 
                user=user_input
            )
            
            from essay_agent.llm_client import call_llm
            raw = call_llm(self.llm, prompt)

            # Short-circuit when offline FakeListLLM returns placeholder ----
            if raw.strip() == "FAKE_RESPONSE":
                return EssayPlan(
                    phase=Phase.BRAINSTORMING,
                    data={"next_tool": "brainstorm", "args": {}},
                )
            
            json_str = raw.strip().splitlines()[-1]
            data = json.loads(json_str)
            tool_name = data.get("tool")
            args = data.get("args", {})
            
            if tool_name not in TOOL_REGISTRY:
                return EssayPlan(
                    phase=_phase_from_tool(tool_name),
                    errors=[f"Unknown tool {tool_name}"],
                    metadata={"llm_raw": raw, "fallback_reason": f"Smart planning failed: {error}"},
                    data={"next_tool": tool_name, "args": args}
                )
            
            phase = _phase_from_tool(tool_name)
            return EssayPlan(
                phase=phase,
                metadata={"llm_raw": raw, "fallback_reason": f"Smart planning failed: {error}"},
                data={"next_tool": tool_name, "args": args}
            )
            
        except Exception:
            # Ultimate fallback
            return EssayPlan(
                errors=[f"Both smart and simple planning failed: {error}"],
                metadata={"llm_raw": raw_response}
            )


def _phase_from_tool(tool: str) -> Phase:
    mapping = {
        "brainstorm": Phase.BRAINSTORMING,
        "outline": Phase.OUTLINING,
        "draft": Phase.DRAFTING,
        "revise": Phase.REVISING,
        "polish": Phase.POLISHING,
        "essay_scoring": Phase.REVISING,  # Evaluation tools map to current phase
        "weakness_highlight": Phase.REVISING,
        "cliche_detection": Phase.REVISING,
        "alignment_check": Phase.REVISING,
    }
    return mapping.get(tool, Phase.BRAINSTORMING) 