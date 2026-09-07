"""
JobAgent V2 Phase 2: Resume Tailoring, Deterministic ATS Scoring, and Document Generation.
"""

from app.resume.resolver import resolve_application_resume
from app.resume.tailor import generate_tailored_resume
from app.resume.storage import (
    load_current_resume_meta,
    save_resume_version,
    update_resume_review_status,
)

__all__ = [
    "resolve_application_resume",
    "generate_tailored_resume",
    "load_current_resume_meta",
    "save_resume_version",
    "update_resume_review_status",
]
