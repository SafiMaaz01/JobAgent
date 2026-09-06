"""Application schemas focusing on jobs, answers, resume, verification, and status.

These models define data transfer objects for the Applications Hub (/api/applications)
and dedicated application detail (/api/applications/{job_id}), tracking package
readiness, resolved candidate answers, resume verification, and automation runner state.
"""
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, ConfigDict


class ApplicationSummary(BaseModel):
    """
    Summary view of an application package used on the Applications Hub page.
    
    Provides job identity, match recommendation, current application package status
    (e.g., 'prepared', 'pending_preparation', 'applied'), and resume availability.
    """
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
    """
    Comprehensive detail model for a single application (/api/applications/{job_id}).
    
    Supplies all data needed for candidate review, form autofill inspection,
    custom question-answering resolution, resume path checks, and live browser automation.
    """
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
    """
    Response returned when triggering package preparation via POST /api/applications/{id}/prepare.
    """
    job_id: int
    status: str
    message: str
    package_file: str

