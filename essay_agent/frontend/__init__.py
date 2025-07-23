"""Essay Agent Debug Frontend

Simple FastAPI-based frontend for visualizing agent internals including:
- Chat interface  
- Memory contents
- Planner decisions
- Tool execution details
- Error logs and debugging info
"""

from .server import app, start_server

__all__ = ["app", "start_server"] 