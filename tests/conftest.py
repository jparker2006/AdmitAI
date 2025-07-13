"""Pytest configuration for test suite.

Ensures that the project root directory is on ``sys.path`` so that the
``essay_agent`` package can be imported when tests are executed from
nested directories such as ``tests/unit`` or ``tests/integration``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add the project root (two levels up from this file) to sys.path *first*
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT)) 