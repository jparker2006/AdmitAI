"""
Base Tool class (optional OOP style)

We start with a lightweight function-based approach, but this abstract base
class provides structure for future expansion.

Key Ideas:
- Validation of input schema (pydantic)
- Standardized output format
- Timeouts & retries
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Tool(ABC):
    """Abstract base class for all tools."""

    name: str  # Each concrete tool should override this

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool logic and return JSON-serializable output.""" 