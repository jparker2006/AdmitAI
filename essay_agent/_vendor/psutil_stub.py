"""Minimal psutil stub used in offline test mode.

Exports the subset of symbols referenced by monitoring.ResourceManager so that
`import psutil` succeeds when the real package is absent.
"""

from __future__ import annotations

import collections

__all__ = [
    "cpu_percent",
    "virtual_memory",
    "disk_usage",
]


def cpu_percent(interval: float | None = None):  # noqa: D401
    return 1.0  # fixed low utilisation


def virtual_memory():  # noqa: D401
    VM = collections.namedtuple("svmem", ["percent"])
    return VM(percent=10.0)


def disk_usage(path: str = "/"):
    DU = collections.namedtuple("sdiskusage", ["percent"])
    return DU(percent=5.0) 