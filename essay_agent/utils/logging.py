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


# ---------------------------------------------------------------------------
# Performance logging utilities
# ---------------------------------------------------------------------------

def performance_log(
    event: str,
    component: str,
    *,
    metrics: dict | None = None,
    level: str = "info"
) -> None:  # noqa: D401
    """Log performance metrics when VERBOSE is enabled.

    Parameters
    ----------
    event : str
        Performance event type (e.g., "resource_allocation", "bottleneck_detected").
    component : str
        Component name (e.g., "orchestrator", "resource_manager").
    metrics : dict | None
        Performance metrics to log.
    level : str
        Log level ("info", "warning", "error").
    """
    if not VERBOSE or JSON_MODE:
        return

    import sys, json as _json, shutil

    use_color = sys.stdout.isatty()
    width = shutil.get_terminal_size((100, 20)).columns

    def _c(txt: str, code: str) -> str:
        return f"{code}{txt}{RESET}" if use_color else txt

    # Choose color based on level
    if level == "warning":
        symbol = _c("⚠", "\033[93m")  # yellow
    elif level == "error":
        symbol = _c("❌", "\033[91m")  # red
    else:
        symbol = _c("📊", "\033[96m")  # cyan

    metrics_str = (
        _json.dumps(metrics, default=str)[:width - 40] + "…"
        if metrics else ""
    )
    
    print(f"{symbol} {component:<12} {event:<20} {metrics_str}")


def resource_trace(
    action: str,
    resource_type: str,
    *,
    utilization: float | None = None,
    available: float | None = None,
    workflow_id: str | None = None
) -> None:  # noqa: D401
    """Trace resource allocation and utilization.

    Parameters
    ----------
    action : str
        Resource action ("allocate", "release", "monitor").
    resource_type : str
        Type of resource ("cpu", "memory", "disk").
    utilization : float | None
        Current utilization percentage.
    available : float | None
        Available resource percentage.
    workflow_id : str | None
        Associated workflow ID.
    """
    if not VERBOSE or JSON_MODE:
        return

    import sys

    use_color = sys.stdout.isatty()

    def _c(txt: str, code: str) -> str:
        return f"{code}{txt}{RESET}" if use_color else txt

    if action == "allocate":
        symbol = _c("⬆", "\033[92m")  # green up arrow
    elif action == "release":
        symbol = _c("⬇", "\033[94m")  # blue down arrow
    else:
        symbol = _c("📈", "\033[96m")  # cyan chart

    workflow_str = f"[{workflow_id[:8]}]" if workflow_id else ""
    util_str = f"{utilization:.1%}" if utilization is not None else ""
    avail_str = f"({available:.1%} available)" if available is not None else ""

    print(f"{symbol} {resource_type:<6} {action:<8} {workflow_str} {util_str} {avail_str}")


def bottleneck_alert(
    bottleneck_type: str,
    component: str,
    *,
    severity: float | None = None,
    recommendation: str | None = None
) -> None:  # noqa: D401
    """Alert about detected performance bottlenecks.

    Parameters
    ----------
    bottleneck_type : str
        Type of bottleneck ("slow_tool", "resource_constraint", etc.).
    component : str
        Affected component name.
    severity : float | None
        Severity score (1.0 = baseline, higher = more severe).
    recommendation : str | None
        Optimization recommendation.
    """
    if not VERBOSE or JSON_MODE:
        return

    import sys, shutil

    use_color = sys.stdout.isatty()
    width = shutil.get_terminal_size((100, 20)).columns

    def _c(txt: str, code: str) -> str:
        return f"{code}{txt}{RESET}" if use_color else txt

    # Choose color based on severity
    if severity and severity > 3.0:
        symbol = _c("🚨", "\033[91m")  # red alert
    elif severity and severity > 1.5:
        symbol = _c("⚠️", "\033[93m")  # yellow warning
    else:
        symbol = _c("🔍", "\033[96m")  # cyan info

    severity_str = f"(severity: {severity:.1f})" if severity else ""
    rec_str = (
        recommendation[:width - 60] + "…" if recommendation and len(recommendation) > width - 60
        else recommendation or ""
    )

    print(f"{symbol} {bottleneck_type:<15} {component:<12} {severity_str}")
    if rec_str:
        print(f"   💡 {rec_str}") 