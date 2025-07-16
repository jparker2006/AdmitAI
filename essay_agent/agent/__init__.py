"""ReAct Agent Package.

This package contains the core ReAct agent implementation for essay writing assistance.
It replaces the complex conversation management system with a clean, intelligent agent
that uses LLM reasoning for all decision-making.
"""

from .core import EssayReActAgent
from .memory import AgentMemory
from .tools import TOOL_DESCRIPTIONS

__all__ = [
    "EssayReActAgent",
    "AgentMemory", 
    "TOOL_DESCRIPTIONS"
]

__version__ = "2.0.0-alpha" 