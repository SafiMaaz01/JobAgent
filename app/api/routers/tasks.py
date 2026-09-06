"""
Background tasks polling and interaction endpoints for JobAgent.

Manages the global in-memory state of running background processes (such as browser autofill):
- `GET /api/tasks/status`: Polled by the frontend (every 1.5s when active) to stream progress, status, and logs.
- `POST /api/tasks/respond`: Sends interactive human input or gate decisions (confirm/cancel/input).
- `POST /api/tasks/cancel`: Gracefully stops the active automation process and closes Chromium.
"""
from fastapi import APIRouter
from app.api.schemas.task import TaskStatus, TaskActionRequest, TaskActionResponse

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

# Global in-memory task state tracker
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
    """
    Update global task state.
    Called by background automation workers to stream progress and status updates.
    """
    _current_task_state["status"] = status
    _current_task_state["message"] = message
    if task is not None:
        _current_task_state["task"] = task
    _current_task_state["progress"] = progress
    _current_task_state["details"] = details


@router.get("/status", response_model=TaskStatus)
def get_task_status():
    """Return current background task status for frontend polling."""
    return TaskStatus(**_current_task_state)


@router.post("/respond", response_model=TaskActionResponse)
def respond_to_task(req: TaskActionRequest):
    """
    Send an interactive response, choice, or gate decision to the active automation task.
    Actions supported: 'confirm' (proceed with submission), 'cancel' (abort submission), 'input' (answer prompt).
    """
    from app.api.automation import automation_manager
    res = automation_manager.respond(action=req.action, value=req.value)
    return TaskActionResponse(**res)


@router.post("/cancel", response_model=TaskActionResponse)
def cancel_task():
    """
    Cancel any active background browser automation task and close the browser safely.
    """
    from app.api.automation import automation_manager
    res = automation_manager.cancel()
    return TaskActionResponse(**res)
