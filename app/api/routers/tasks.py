"""Background tasks polling and status endpoint."""
from fastapi import APIRouter
from app.api.schemas.task import TaskStatus, TaskActionRequest, TaskActionResponse

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


@router.post("/respond", response_model=TaskActionResponse)
def respond_to_task(req: TaskActionRequest):
    """Send interactive response or decision to the active automation task."""
    from app.api.automation import automation_manager
    res = automation_manager.respond(action=req.action, value=req.value)
    return TaskActionResponse(**res)


@router.post("/cancel", response_model=TaskActionResponse)
def cancel_task():
    """Cancel any active background automation task."""
    from app.api.automation import automation_manager
    res = automation_manager.cancel()
    return TaskActionResponse(**res)
