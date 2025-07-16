"""Base classes and utilities for essay agent tools."""
from __future__ import annotations

import asyncio
import functools
import logging
import time
import traceback
from abc import ABC
from typing import Any, Dict, Optional, Union

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, ValidationError
from essay_agent.llm_client import get_chat_llm
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

                return {"ok": result, "error": None}
            except asyncio.TimeoutError as exc:
                last_error = exc
                attempt += 1
                print(f"⏰ Tool '{self.name}' timed out on attempt {attempt}/{self.max_attempts}")
                
                if attempt >= self.max_attempts:
                    # Provide graceful degradation for timeout errors
                    return self._handle_timeout_fallback(*args, **kwargs)
                    
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                attempt += 1
                print(f"⚠️  Tool '{self.name}' failed on attempt {attempt}/{self.max_attempts}: {type(exc).__name__}")
                
                if attempt >= self.max_attempts:
                    return {"ok": None, "error": _format_exc(exc)}

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

        return {"ok": None, "error": _format_exc(last_error) if last_error else "Unknown error"}

    async def ainvoke(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:  # type: ignore[override]
        try:
            coro = self._arun_wrapper(*args, **kwargs)
            if self.timeout is not None:
                coro = asyncio.wait_for(coro, timeout=self.timeout)
            result = await coro
            return {"ok": result, "error": None}
        except Exception as exc:  # noqa: BLE001
            return {"ok": None, "error": _format_exc(exc)}

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


def _format_exc(exc: Exception) -> ToolError:
    return ToolError(type=exc.__class__.__name__, message=str(exc), trace="".join(traceback.format_tb(exc.__traceback__))) 