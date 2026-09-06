"""Job schemas."""
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, ConfigDict


class JobSummary(BaseModel):
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
    review_status: str = "pending"
    reviewed_at: Optional[str] = None
    applied_at: Optional[str] = None
    has_application: bool = False

    model_config = ConfigDict(from_attributes=True)


class JobDetail(JobSummary):
    description: Optional[str] = None
    matched_at: Optional[str] = None
    match_details: Optional[Dict[str, Any]] = None
    application_status: Optional[str] = None


class JobListResponse(BaseModel):
    items: List[JobSummary]
    total: int
    page: int
    limit: int
    pages: int


class ReviewRequest(BaseModel):
    status: str  # "approved" | "rejected" | "pending"


class ReviewResponse(BaseModel):
    id: int
    review_status: str
    reviewed_at: Optional[str] = None
    message: str

