"""Background tasks polling and status endpoint."""
from fastapi import APIRouter
from app.api.schemas.task import TaskStatus

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

# In-memory task state tracker
_current_task_state = {
    "task": None,
    "status": "idle",
    "message": "No active task",
    "progress": 0,
    "details": None,
}


def get_task_state() -> dict:
    """Return the global task state dictionary."""
    return _current_task_state


def update_task_state(status: str, message: str, task: str = None, progress: int = 0, details: dict = None):
    """Update global task state."""
    _current_task_state["status"] = status
    _current_task_state["message"] = message
    if task is not None:
        _current_task_state["task"] = task
    _current_task_state["progress"] = progress
    _current_task_state["details"] = details


@router.get("/status", response_model=TaskStatus)
def get_task_status():
    """Return current background task status for polling."""
    return TaskStatus(**_current_task_state)
