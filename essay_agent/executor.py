"""
EssayExecutor - Executes Planner-generated Plans

Responsibilities:
1. Validate plan structure
2. Map tasks to concrete Tool calls
3. Orchestrate parallel execution where possible
4. Aggregate tool outputs and format replies

TODO:
- Implement dynamic import / registry for tools
- Add error handling & retries
- Integrate concurrency (asyncio / multiprocessing) for parallel tool runs
"""

from typing import Dict, Any, Callable

from .tools import TOOL_REGISTRY
from .planner import Plan


class EssayExecutor:
    """Lightweight executor for MVP."""

    def __init__(self):
        # Dependency injection point for advanced logging, tracing, etc.
        self.registry = TOOL_REGISTRY

    def run_plan(self, plan: Plan) -> Dict[str, Any]:
        """Execute tasks sequentially (MVP).

        Args:
            plan: Plan object from EssayPlanner
        Returns:
            Dict[str, Any]: Mapping of task → output or error message
        """
        outputs: Dict[str, Any] = {}
        for task_name in plan.tasks:
            tool: Callable = self.registry.get(task_name)
            if tool is None:
                outputs[task_name] = {
                    "error": f"Tool '{task_name}' not found in registry"
                }
                continue
            try:
                outputs[task_name] = tool()
            except Exception as exc:  # pragma: no cover – improve specific handling later
                outputs[task_name] = {"error": str(exc)}
        return outputs 