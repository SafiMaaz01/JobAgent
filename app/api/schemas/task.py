"""Task status schemas."""
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict


class TaskStatus(BaseModel):
    task: Optional[str] = None
    status: str = "idle"  # idle | running | completed | error
    message: str = "No active task"
    progress: int = 0
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
