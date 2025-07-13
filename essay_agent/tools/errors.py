"""Error dataclasses for tool execution.
"""
from pydantic import BaseModel
from typing import Optional

class ToolError(BaseModel):
    """Standardized error payload returned by tool infrastructure."""

    type: str
    message: str
    trace: Optional[str] = None 