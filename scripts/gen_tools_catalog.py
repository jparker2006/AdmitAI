#!/usr/bin/env python
"""Generate docs/tools_catalog.md with metadata for every registered tool.

Usage::

    python scripts/gen_tools_catalog.py

Re-runs are idempotent – if the registry hasn't changed the output file will
be identical, so CI will show no diff.  The script is lightweight and has no
third-party dependencies beyond what the project already installs.
"""
from __future__ import annotations

import inspect
import os
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence

# Ensure project root on sys.path when script executed directly -------------
import sys

if "essay_agent" not in sys.modules:
    root_dir = Path(__file__).resolve().parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

from essay_agent.tools import REGISTRY as TOOL_REGISTRY

ROOT = Path(__file__).resolve().parent.parent
DOCS_PATH = ROOT / "docs" / "tools_catalog.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_description(tool) -> str:  # noqa: D401
    return (getattr(tool, "description", None) or tool.__doc__ or "-").strip()


def _get_phases(tool) -> str:  # noqa: D401
    phases: Sequence[str] | str | None = (
        getattr(tool, "phase", None) or getattr(tool, "phases", None)
    )
    if phases is None:
        return "-"
    if isinstance(phases, (list, tuple, set)):
        return ", ".join(str(p) for p in phases)
    return str(phases)


def _get_required_args(tool) -> str:  # noqa: D401
    # LangChain BaseTool may expose args_schema (Pydantic BaseModel)
    schema = getattr(tool, "args_schema", None)
    if schema is not None:
        required_fields = [name for name, f in schema.model_fields.items() if f.is_required()]
        return ", ".join(required_fields) or "-"

    # Fallback to inspect the _run signature -----------------------------
    run_fn = None
    for cand in ("_run", "__call__"):
        if hasattr(tool, cand):
            run_fn = getattr(tool, cand)
            break
    if run_fn is None:
        return "-"

    sig = inspect.signature(run_fn)
    params: List[str] = []
    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue
        # consider parameter required if no default
        if param.default is inspect.Parameter.empty and param.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            params.append(name)
    return ", ".join(params) or "-"


def main() -> None:  # noqa: D401
    rows: List[Dict[str, Any]] = []
    for name, tool in TOOL_REGISTRY.items():
        rows.append(
            {
                "Tool": name,
                "Description": _get_description(tool).replace("\n", " ").strip(),
                "Phase(s)": _get_phases(tool),
                "Required Args": _get_required_args(tool),
                "Return": "dict(ok/error)"  # placeholder – manual later
            }
        )

    # Sort alphabetically for stable diff --------------------------------
    rows.sort(key=lambda r: r["Tool"].lower())

    # Build markdown table -----------------------------------------------
    headers = ["Tool", "Description", "Phase(s)", "Required Args", "Return"]
    md_lines = []
    md_lines.append("# Essay Agent – Tool Catalog\n")
    md_lines.append(f"_Generated: {datetime.utcnow().isoformat(timespec='seconds')} UTC_\n")
    md_lines.append("")

    # Header row
    md_lines.append("| " + " | ".join(headers) + " |")
    md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in rows:
        md_lines.append("| " + " | ".join(row[h] for h in headers) + " |")

    content = "\n".join(md_lines) + "\n"

    # Ensure docs/ directory exists --------------------------------------
    DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCS_PATH.write_text(content, encoding="utf-8")
    print(f"[OK] Wrote {DOCS_PATH.relative_to(ROOT)} with {len(rows)} tools.")


if __name__ == "__main__":
    main() 