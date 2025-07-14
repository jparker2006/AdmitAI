from __future__ import annotations

import sys
from datetime import datetime
from typing import Any

COLOR = "\033[96m"  # cyan
RESET = "\033[0m"

# ---------------------------------------------------------------------------
# Verbose / JSON flags are toggled by the CLI so lower-level modules don’t
# need to know about argument parsing.
# ---------------------------------------------------------------------------

VERBOSE: bool = False  # set True by --verbose flag
JSON_MODE: bool = False  # set True automatically when --json chosen


def debug_print(enabled: bool, message: str, *, file: Any = sys.stdout) -> None:  # noqa: D401
    """Conditionally print *message* with timestamp when *enabled*.

    Keeps console noise under control while giving rich debug capability.
    """
    if not enabled:
        return
    timestamp = datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
    print(f"{COLOR}[{timestamp}] {message}{RESET}", file=file)


def tool_trace(
    event: str,
    tool: str,
    *,
    args: dict | None = None,
    elapsed: float | None = None,
    error: str | None = None,
) -> None:  # noqa: D401
    """Print a colourised trace line when VERBOSE is enabled.

    Parameters
    ----------
    event : str
        One of ``start``, ``end``, ``error``.
    tool : str
        Tool name.
    args : dict | None
        Arguments (only shown on *start*).
    elapsed : float | None
        Seconds between start/end (only shown on *end*).
    error : str | None
        Error string (only on *error*).
    """

    if not VERBOSE or JSON_MODE:
        return

    import sys, json as _json, shutil

    use_color = sys.stdout.isatty()
    width = shutil.get_terminal_size((100, 20)).columns  # graceful fallback

    def _c(txt: str, code: str) -> str:
        return f"{code}{txt}{RESET}" if use_color else txt

    if event == "start":
        arrow = _c("▶", "\033[94m")  # blue
        arg_str = (
            _json.dumps(args, default=str)[:width - 40] + "…"
            if args else ""
        )
        print(f"{arrow} {tool:<12} {arg_str}")

    elif event == "end":
        check = _c("✔", "\033[92m")  # green
        timing = f"{elapsed:.2f} s" if elapsed is not None else ""
        print(f"{check} {tool:<12} {timing}")

    elif event == "error":
        cross = _c("✖", "\033[91m")  # red
        err = (error or "")[: width - 20]
        print(f"{cross} {tool:<12} {err}")

    else:  # pragma: no cover – unknown event
        print(f"{tool}: {event}") 