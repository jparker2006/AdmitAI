from __future__ import annotations

import sys
from datetime import datetime
from typing import Any

COLOR = "\033[96m"  # cyan
RESET = "\033[0m"

def debug_print(enabled: bool, message: str, *, file: Any = sys.stdout) -> None:  # noqa: D401
    """Conditionally print *message* with timestamp when *enabled*.

    Keeps console noise under control while giving rich debug capability.
    """
    if not enabled:
        return
    timestamp = datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
    print(f"{COLOR}[{timestamp}] {message}{RESET}", file=file) 