"""Error dataclasses for tool execution.
"""
from pydantic import BaseModel
from typing import Optional

class ToolError(BaseModel):
    """Standardized error payload returned by tool infrastructure."""

    type: str
    message: str
    trace: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation for JSON serialization."""
        return f"{self.type}: {self.message}"
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            # Ensure proper JSON serialization
            str: lambda v: v
        } 