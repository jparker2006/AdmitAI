"""Base classes for LangChain tools with validation & timeout wrappers."""

from __future__ import annotations

import asyncio
import traceback
from abc import ABC
from typing import Any, Dict, Optional

from langchain.tools import BaseTool
from pydantic import ValidationError

from essay_agent.tools.errors import ToolError


class ValidatedTool(BaseTool, ABC):
    """Base class adding timeout & standardized error handling.

    Subclasses implement ``_run`` and optionally ``_arun``.
    """

    # Tools will often return dicts that are already JSON-serialisable
    return_direct: bool = True

    # Maximum seconds to allow; ``None`` means no limit.
    timeout: Optional[float] = 5.0

    # ---------------------------------------------------------------------
    # Public call wrappers
    # ---------------------------------------------------------------------

    def __call__(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:  # type: ignore[override]
        try:
            if self.timeout is not None:
                loop = asyncio.new_event_loop()
                result = loop.run_until_complete(
                    asyncio.wait_for(self._arun_wrapper(*args, **kwargs), timeout=self.timeout)
                )
            else:
                result = self._run(*args, **kwargs)

            return {"ok": result, "error": None}
        except Exception as exc:  # noqa: BLE001
            return {"ok": None, "error": _format_exc(exc)}

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


def _format_exc(exc: Exception) -> ToolError:
    return ToolError(type=exc.__class__.__name__, message=str(exc), trace="".join(traceback.format_tb(exc.__traceback__))) 