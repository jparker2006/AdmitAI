"""Base classes and utilities for essay agent tools."""
from __future__ import annotations

import asyncio
import functools
import logging
import time
import traceback
from abc import ABC
from typing import Any, Dict, Optional, Union
import re

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, ValidationError
from essay_agent.llm_client import get_chat_llm
from essay_agent.utils.json_repair import fix as repair_json
from essay_agent.tools.errors import ToolError


logger = logging.getLogger(__name__)


def safe_model_to_dict(result: Any) -> Dict[str, Any]:
    """Safely convert tool result to dictionary.
    
    Handles both Pydantic models and plain dictionaries returned by parsers.
    
    Args:
        result: Result from LLM parsing (could be Pydantic model or dict)
        
    Returns:
        Dictionary representation of the result
    """
    if hasattr(result, 'model_dump'):
        # Pydantic model with model_dump method
        return result.model_dump()
    elif isinstance(result, dict):
        # Already a dictionary
        return result
    elif hasattr(result, 'dict'):
        # Older Pydantic model with dict method
        return result.dict()
    else:
        # Fallback: try to convert to dict
        try:
            return dict(result)
        except (TypeError, ValueError):
            # Last resort: wrap in a dict
            return {"result": result}


class ValidatedTool(BaseTool, ABC):
    """Base class adding timeout & standardized error handling.

    Subclasses implement ``_run`` and optionally ``_arun``.
    """

    # Tools will often return dicts that are already JSON-serialisable
    return_direct: bool = True

    # Maximum seconds to allow; ``None`` means no limit.
    import os as _os
    timeout: Optional[float] = float(_os.getenv("ESSAY_AGENT_TOOL_TIMEOUT", "45"))

    # Maximum attempts for retries (including the initial try)
    max_attempts: int = 3

    # ---------------------------------------------------------------------
    # Public call wrappers
    # ---------------------------------------------------------------------

    def __call__(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:  # type: ignore[override]
        """Synchronous entry point with exponential-backoff retry on failure."""

        attempt = 0
        delay = 2.0  # seconds (doubles each retry, starting higher)
        last_error = None
        
        while attempt < self.max_attempts:
            try:
                if self.timeout is not None:
                    # Check if we're already in an async context
                    try:
                        loop = asyncio.get_running_loop()
                        # We're in an async context, just use sync version for now
                        # TODO: Implement proper async tool execution
                        result = self._run(*args, **kwargs)
                    except RuntimeError:
                        # No running loop, create new one
                        result = asyncio.run(
                            asyncio.wait_for(self._arun_wrapper(*args, **kwargs), timeout=self.timeout)
                        )
                else:
                    result = self._run(*args, **kwargs)

                return {"ok": safe_model_to_dict(result), "error": None}
            except asyncio.TimeoutError as exc:
                last_error = exc
                attempt += 1
                print(f"⏰ Tool '{self.name}' timed out on attempt {attempt}/{self.max_attempts}")
                
                if attempt >= self.max_attempts:
                    # Provide graceful degradation for timeout errors
                    fb = self._handle_timeout_fallback(*args, **kwargs)
                    return {"ok": safe_model_to_dict(fb.get("ok")), "error": fb.get("error")}
                    
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                attempt += 1
                print(f"⚠️  Tool '{self.name}' failed on attempt {attempt}/{self.max_attempts}: {type(exc).__name__}")
                
                if attempt >= self.max_attempts:
                    return {"ok": None, "error": safe_model_to_dict(_format_exc(exc))}

            # Exponential backoff with longer delays
            if attempt < self.max_attempts:
                import time, os
                if os.getenv('ESSAY_AGENT_FAST_TEST', '0') == '1':
                    # Skip real sleeping to keep tests fast
                    print("🔄 Retrying immediately (FAST_TEST mode)...")
                    time.sleep(0.01)
                else:
                    print(f"🔄 Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    delay = min(delay * 2, 16.0)  # cap the wait to 16s

        return {"ok": None, "error": safe_model_to_dict(_format_exc(last_error)) if last_error else "Unknown error"}

    async def ainvoke(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:  # type: ignore[override]
        try:
            coro = self._arun_wrapper(*args, **kwargs)
            if self.timeout is not None:
                coro = asyncio.wait_for(coro, timeout=self.timeout)
            result = await coro
            return {"ok": safe_model_to_dict(result), "error": None}
        except Exception as exc:  # noqa: BLE001
            return {"ok": None, "error": safe_model_to_dict(_format_exc(exc))}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _arun_wrapper(self, *args: Any, **kwargs: Any):  # noqa: D401
        # Default implementation delegates to sync _run in thread.
        return await asyncio.to_thread(self._run, *args, **kwargs)

    def _handle_timeout_fallback(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Provide graceful degradation when tool times out completely.
        
        Subclasses can override this to provide tool-specific fallback behavior.
        """
        error_msg = f"Tool '{self.name}' timed out after {self.max_attempts} attempts with {self.timeout}s timeout"
        
        # Provide helpful context about what failed
        fallback_result = {
            "tool_name": self.name,
            "timeout_seconds": self.timeout,
            "max_attempts": self.max_attempts,
            "fallback_reason": "timeout",
            "suggested_action": f"Consider increasing timeout or simplifying the request to {self.name}"
        }
        
        return {"ok": fallback_result, "error": error_msg}

    # ------------------------------------------------------------------
    # Shared helper for LLM + parser execution (used by many tools)
    # ------------------------------------------------------------------

    def _call_llm_with_prompt_and_parser(
        self,
        llm,
        *,
        prompt_text: str,
        parser,
        required_keys: list[str] | None = None,
    ) -> Dict[str, Any]:  # noqa: D401,E501
        """Utility that sends *prompt_text* to *llm* and returns parsed dict.

        This centralises the common pattern of:
        1. Call the LLM with a prompt
        2. Parse the raw response with a pydantic_parser / OutputParser
        3. Convert the parsed model (or dict) into a plain ``dict`` so that
           downstream code can safely JSON-serialize the result.

        It also supports the deterministic offline-testing path controlled by
        the ``ESSAY_AGENT_OFFLINE_TEST`` environment variable.  In that mode we
        skip the real LLM call and instead return an empty instance parsed by
        the provided *parser*, ensuring unit tests remain fast and reliable.
        """
        import os
        from essay_agent.llm_client import call_llm
        from essay_agent.response_parser import safe_parse

        # Offline stub path ------------------------------------------------
        if os.getenv("ESSAY_AGENT_OFFLINE_TEST") == "1":
            try:
                # Attempt to create a blank instance via parser for schema shape
                blank_json = "{}"
                parsed = safe_parse(parser, blank_json)
                return safe_model_to_dict(parsed)
            except Exception:
                # Fallback to empty dict if parser cannot handle blank input
                return {}

        # Online path – actual LLM call ------------------------------------
        raw = call_llm(llm, prompt_text)
        raw = _strip_fences(raw)
        # Debug raw LLM response when flag enabled -------------------------
        import os, textwrap
        if os.getenv("ESSAY_AGENT_SHOW_RAW") == "1":
            from essay_agent.utils.logging import debug_print, VERBOSE
            snippet = textwrap.shorten(raw.replace("\n", " "), width=500, placeholder="…")
            debug_print(True, f"RAW LLM → {self.name}: {snippet}")
        # Attempt parse ---------------------------------------------------
        try:
            parsed = safe_parse(parser, raw)
            out_dict = safe_model_to_dict(parsed)
        except Exception:
            # Centralised schema-aware repair -----------------------------
            from essay_agent.tools.schema_registry import TOOL_OUTPUT_SCHEMA

            schema_text = TOOL_OUTPUT_SCHEMA.get(self.name, "")
            rep_raw = repair_json(raw, schema_text)

            try:
                parsed = safe_parse(parser, rep_raw)
                out_dict = safe_model_to_dict(parsed)
            except Exception:
                fb = self._handle_timeout_fallback()
                return safe_model_to_dict(fb.get("ok"))

        # ----------------- Validate required keys (post-repair) -------------
        if required_keys:
            missing = [k for k in required_keys if k not in out_dict or out_dict[k] in (None, [], {})]
            if missing:
                # Centralised schema-aware repair -----------------------------
                from essay_agent.tools.schema_registry import TOOL_OUTPUT_SCHEMA

                schema_text = TOOL_OUTPUT_SCHEMA.get(self.name, "")
                rep_raw = repair_json(raw, schema_text)

                try:
                    parsed = safe_parse(parser, rep_raw)
                    out_dict = safe_model_to_dict(parsed)
                    missing = [k for k in required_keys if k not in out_dict or out_dict[k] in (None, [], {})]
                except Exception:
                    missing = required_keys  # force fallback

            if missing:
                fb = self._handle_timeout_fallback()
                return safe_model_to_dict(fb.get("ok"))

        return out_dict


def _format_exc(exc: Exception) -> ToolError:
    return ToolError(type=exc.__class__.__name__, message=str(exc), trace="".join(traceback.format_tb(exc.__traceback__))) 


# ---------------------------------------------------------------------------
# Helper: strip markdown code fences (```json ... ```)
# ---------------------------------------------------------------------------


_FENCE_RE = re.compile(r"^```(?:[a-zA-Z0-9]+)?\s*(.*?)\s*```$", re.DOTALL)


def _strip_fences(text: str) -> str:  # noqa: D401
    """Return *text* without outer ``` fences if present.

    Works with or without a language hint (```json, ```python, etc.).  If no
    matching fences are found the text is returned unchanged.
    """
    if not isinstance(text, str):
        return text  # leave non-str untouched

    stripped = text.strip()
    match = _FENCE_RE.match(stripped)
    if match:
        return match.group(1).strip()
    return text 