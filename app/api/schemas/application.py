"""Application schemas focusing on jobs, answers, resume, verification, and status."""
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, ConfigDict


class ApplicationSummary(BaseModel):
    job_id: int
    company: str
    title: str
    location: Optional[str] = None
    match_score: Optional[int] = None
    recommendation: Optional[str] = None
    review_status: Optional[str] = None
    application_status: str
    has_resume: bool = False
    created_at: Optional[str] = None
    applied_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationDetail(BaseModel):
    job_id: int
    company: str
    role: str
    location: Optional[str] = None
    match_score: Optional[int] = None
    recommendation: Optional[str] = None
    review_status: Optional[str] = None
    job_url: str
    job_description: Optional[str] = None
    application_status: str
    resume_path: Optional[str] = None
    resume_exists: bool = False
    resolved_answers: Dict[str, Any] = {}
    candidate: Optional[Dict[str, Any]] = None
    match_details: Optional[Dict[str, Any]] = None
    automation_status: str = "idle"
    verification_status: str = "not_run"
    verification_checks: List[Dict[str, Any]] = []
    submission_state: str = "pending"
    created_at: Optional[str] = None
    applied_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PreparePackageResponse(BaseModel):
    job_id: int
    status: str
    message: str
    package_file: str
