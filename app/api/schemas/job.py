"""Job schemas for API request and response serialization.

These Pydantic models define the data shapes returned by the /api/jobs endpoints,
including job summaries, detailed match breakdowns, and human review actions.
"""
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, ConfigDict


class JobSummary(BaseModel):
    """
    Lightweight job summary returned in listing endpoints and dashboards.
    
    Includes core job metadata, match recommendation scores from local AI,
    human review status (pending, approved, rejected), and whether an application
    package has already been generated.
    """
    id: int
    source: str
    external_id: str
    company: str
    title: str
    location: Optional[str] = None
    url: str
    posted_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_relevant: int = 0
    match_score: Optional[int] = None
    recommendation: Optional[str] = None
    review_status: str = "pending"  # "pending" | "approved" | "rejected"
    reviewed_at: Optional[str] = None
    applied_at: Optional[str] = None
    has_application: bool = False

    # Enable ORM mode so Pydantic can read attributes from sqlite3.Row dicts
    model_config = ConfigDict(from_attributes=True)


class JobDetail(JobSummary):
    """
    Detailed job model returned when viewing a specific job (/api/jobs/{id}).
    
    Includes full job description, parsed AI matching details (e.g. strong matches,
    missing requirements, concerns, reasoning), and application status if prepared.
    """
    description: Optional[str] = None
    matched_at: Optional[str] = None
    match_details: Optional[Dict[str, Any]] = None
    application_status: Optional[str] = None


class JobListResponse(BaseModel):
    """
    Paginated response container for job queries with pagination metadata.
    """
    items: List[JobSummary]
    total: int
    page: int
    limit: int
    pages: int


class ReviewRequest(BaseModel):
    """
    Payload for updating human review status on a job (approve/reject).
    """
    status: str  # "approved" | "rejected" | "pending"


class ReviewResponse(BaseModel):
    """
    Response returned following a successful review decision update.
    """
    id: int
    review_status: str
    reviewed_at: Optional[str] = None
    message: str


