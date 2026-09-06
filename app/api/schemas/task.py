"""Task status schemas for background browser automation monitoring and interaction.

These models allow the frontend to poll for automation progress, inspect step-by-step
logs, detect waiting gates (such as the Ready to Submit human review prompt), and send
user decisions (confirm submission or cancel).
"""
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict


class TaskStatus(BaseModel):
    """
    Current status of the background browser automation task.
    
    Attributes:
        task: Identifier of the running task (e.g. 'autofill_app_474').
        status: State enum ('idle', 'running', 'waiting_for_confirmation',
                'waiting_for_input', 'completed', 'cancelled', 'error').
        message: Human-readable message describing what step is currently executing.
        progress: Percentage completion estimate (0 - 100).
        details: Additional contextual data (e.g., job_id, recent log lines, error messages).
    """
    task: Optional[str] = None
    status: str = "idle"  # idle | running | waiting_for_confirmation | waiting_for_input | completed | cancelled | error
    message: str = "No active task"
    progress: int = 0
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class TaskActionRequest(BaseModel):
    """
    Action sent by the user to interact with a waiting automation task.
    
    Attributes:
        action: 'confirm' to approve final form submission, 'cancel' to abort, or 'input' for answers.
        value: Optional string input payload (e.g. 'y' / 'n').
    """
    action: str  # "cancel" | "confirm" | "input"
    value: Optional[str] = None


class TaskActionResponse(BaseModel):
    """
    Acknowledgment returned after dispatching a task action request.
    """
    success: bool
    message: str

