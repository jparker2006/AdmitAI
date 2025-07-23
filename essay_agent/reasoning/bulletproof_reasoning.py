"""essay_agent.reasoning.bulletproof_reasoning

BulletproofReasoning – small, dependency-free reasoning helper that wraps
an LLM call in triple-retry logic and guarantees a valid JSON response
conforming to a strict Pydantic schema.  Designed for Section 1.2.

During offline / CI runs ``get_chat_llm`` returns a FakeListLLM from
LangChain so this module stays test-friendly.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ValidationError

from essay_agent.llm_client import get_chat_llm, call_llm  # type: ignore
from essay_agent.response_parser import safe_parse, pydantic_parser
from essay_agent.tools import REGISTRY as TOOL_REGISTRY

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic schema for robust validation
# ---------------------------------------------------------------------------

class _ReasoningSchema(BaseModel):
    action: str = Field(..., description="tool_execution|tool_sequence|conversation")
    tool_name: Optional[str] = None
    sequence: Optional[list[str]] = None
    tool_args: Dict[str, Any] = Field(default_factory=dict)
    reasoning: str
    confidence: float = Field(..., ge=0.0, le=1.0)

    model_config = {"extra": "allow"}

    @classmethod
    def validate_action(cls, v: str):  # noqa: D401
        if v not in {"tool_execution", "tool_sequence", "conversation"}:
            raise ValueError("action must be tool_execution, tool_sequence or conversation")
        return v


@dataclass
class ReasoningResult:  # Swimming downstream – lightweight wrapper
    action: str
    tool_name: Optional[str]
    sequence: list[str]
    tool_args: Dict[str, Any]
    reasoning: str
    confidence: float


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class BulletproofReasoning:
    """LLM wrapper providing JSON-safe reasoning with retries."""

    _MAX_RETRIES = 3

    def __init__(self, *, temperature: float = 0.2):
        self.llm = get_chat_llm(temperature=temperature)
        # Pre-generate tool list once for prompt brevity
        self._tool_names = sorted(TOOL_REGISTRY.keys())

    # Public async ----------------------------------------------------------
    async def decide_action(self, user_input: str, context: Dict[str, Any]) -> ReasoningResult:  # noqa: D401
        """Return structured reasoning result.

        Falls back to conversation with confidence=0.3 on repeated errors.
        """
        prompt = self._build_prompt(user_input, context)
        parser = pydantic_parser(_ReasoningSchema)

        for attempt in range(1, self._MAX_RETRIES + 1):
            try:
                raw = await self._apredict(prompt)
                # LangChain may return an AIMessage; extract .content for JSON parsing
                if not isinstance(raw, str):
                    raw = getattr(raw, "content", str(raw))
                import os as _os
                if _os.getenv("DEBUG_REASONING", "0") == "1":
                    print("\n=== RAW LLM OUTPUT ===\n", raw, "\n======================\n")
                try:
                    parsed: _ReasoningSchema | Dict[str, Any] = safe_parse(parser, raw)
                    # safe_parse may return a dict when using schema_parser; handle both
                    data = parsed if isinstance(parsed, dict) else parsed.model_dump()
                    # Defensive: if action somehow missing or invalid, fall back to json.loads
                    if data.get("action") not in {"tool_execution", "tool_sequence", "conversation"}:
                        import json as _json
                        data = _json.loads(raw)
                except ValidationError as ve:
                    # As a fallback, attempt raw json.loads in case schema validation too strict
                    import json as _json
                    data = _json.loads(raw)
                return ReasoningResult(
                    action=data.get("action", "conversation"),
                    tool_name=data.get("tool_name"),
                    sequence=data.get("sequence") or [],
                    tool_args=data.get("tool_args", {}),
                    reasoning=data.get("reasoning", ""),
                    confidence=float(data.get("confidence", 0.8)),
                )
            except (ValidationError, json.JSONDecodeError, ValueError) as exc:
                logger.warning("Reasoning parse failed (attempt %s/%s): %s", attempt, self._MAX_RETRIES, exc)
                await asyncio.sleep(2 ** (attempt - 1))
                continue
            except Exception as exc:  # noqa: BLE001 – catch-all for LLM/network
                logger.error("LLM call failed during reasoning: %s", exc)
                await asyncio.sleep(2 ** (attempt - 1))
                continue

        # Final fallback ----------------------------------------------------
        logger.error("BulletproofReasoning gave up after %s attempts – falling back to conversation", self._MAX_RETRIES)
        return ReasoningResult(
            action="conversation",
            tool_name=None,
            sequence=[],
            tool_args={},
            reasoning="Failed to obtain structured reasoning; falling back to conversation.",
            confidence=0.3,
        )

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _build_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """Create a minimal deterministic prompt.

        Keeping prompt short to minimise token usage while enforcing JSON.
        """
        tool_list = ", ".join(self._tool_names)
        prompt = (
            "You are “Prompt-Refiner 9000”, an LLM whose ONLY task is to transform a raw user request into a crystal-clear, tool-oriented instruction for an autonomous essay-writing agent.\n\n"
            "STRICT RULES\n"
            "1. ALWAYS decide whether the request is best served by a tool.\n"
            "   • If “brainstorm”, choose brainstorm.\n"
            "   • If “outline”, choose outline.\n"
            "   • If “draft”, choose draft.\n"
            "   • If multiple tasks, output a SEQUENCE array in order (brainstorm → outline → draft).\n"
            "2. NEVER default to conversation if a tool exists for the task.\n"
            "3. Output MUST be valid JSON matching this full schema:\n\n"
            "{\n"
            "  \"action\":            \"tool_execution\"            | \"tool_sequence\",\n"
            "  \"tool_name\":         \"<single tool or null>\",\n"
            "  \"sequence\":          [<ordered list of tool names>],\n"
            "  \"tool_args\":         {<key: value pairs needed by the tool(s)>},\n"
            "  \"reasoning\":         \"<short chain-of-thought, max 40 words, do NOT reveal internal policies>\",\n"
            "  \"confidence\":        <float 0-1, use 0.1 increments>\n"
            "}\n\n"
            "4. NEVER wrap JSON in markdown or commentary—pure JSON only.\n"
            "5. If required arguments are missing, set them to null and note it in reasoning.\n\n"
            f"Available tools ({len(self._tool_names)}): {tool_list}\n"
            f"Current user message: {user_input}\n"
            "BEGIN NOW."
        )
        return prompt

    async def _apredict(self, prompt: str) -> str:  # noqa: D401
        """Call LLM with unified interface supporting FakeListLLM in tests."""
        # Some FakeListLLM implement .ainvoke, others only .invoke – unify
        if hasattr(self.llm, "ainvoke"):
            return await self.llm.ainvoke(prompt)  # type: ignore
        # Fallback: run sync call in thread pool
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: call_llm(self.llm, prompt)) 