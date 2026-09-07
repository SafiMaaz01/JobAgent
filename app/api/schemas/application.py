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
    submission_source: Optional[str] = None

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
    submission_source: Optional[str] = None
    tailored_resume: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class MarkSubmittedResponse(BaseModel):
    """
    Response returned when manually marking an application as submitted.
    """
    job_id: int
    application_status: str
    review_status: str
    applied_at: Optional[str] = None
    submission_source: Optional[str] = None
    message: str
    already_submitted: bool = False


class PreparePackageResponse(BaseModel):
    """
    Response returned when triggering package preparation via POST /api/applications/{id}/prepare.
    """
    job_id: int
    status: str
    message: str
    package_file: str


class TailoredResumeDetail(BaseModel):
    """
    Detail schema for tailored resume metadata and ATS breakdown.
    """
    job_id: int
    current_version: Optional[int] = None
    status: str
    approved_version: Optional[int] = None
    ats_score: Optional[int] = None
    score_category: Optional[str] = None
    docx_path: Optional[str] = None
    pdf_path: Optional[str] = None
    last_generated_at: Optional[str] = None
    review_feedback: Optional[str] = None
    ats_analysis: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None
    resume_data: Optional[Dict[str, Any]] = None


class ResumeGenerateResponse(BaseModel):
    """
    Response model for resume generation endpoint.
    """
    job_id: int
    version: int
    status: str
    ats_score: int
    docx_path: str
    pdf_path: str
    validation: Dict[str, Any]
    ats_analysis: Dict[str, Any]
    message: str


class ResumeReviewRequest(BaseModel):
    """
    Request model for human review gate.
    """
    status: str  # "approved" | "rejected"
    feedback: Optional[str] = None


class ResumeReviewResponse(BaseModel):
    """
    Response model for human review gate.
    """
    job_id: int
    status: str
    current_version: int
    approved_version: Optional[int] = None
    message: str


