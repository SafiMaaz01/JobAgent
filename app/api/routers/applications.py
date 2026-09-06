"""Applications endpoints for inspecting prepared and submitted application packages."""
import json
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException
from app.api.schemas.application import ApplicationDetail, ApplicationSummary

router = APIRouter(prefix="/api/applications", tags=["Applications"])

APPLICATIONS_DIR = Path("data/applications")


def check_resume_exists(resume_path_str: str | None) -> bool:
    """Check if resume file actually exists on filesystem."""
    if not resume_path_str:
        return False
    path = Path(resume_path_str)
    return path.exists()


@router.get("", response_model=List[ApplicationSummary])
def list_applications():
    """List all application packages found in data/applications/."""
    if not APPLICATIONS_DIR.exists():
        return []

    summaries = []
    for file in APPLICATIONS_DIR.glob("job_*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                pkg = json.load(f)

            job = pkg.get("job", {})
            app_meta = pkg.get("application", {})

            job_id = job.get("id")
            if job_id is None:
                # Try inferring from filename job_<id>.json
                stem = file.stem.split("_")
                if len(stem) == 2 and stem[1].isdigit():
                    job_id = int(stem[1])
                else:
                    continue

            status = app_meta.get("status", "unknown")
            created_at = app_meta.get("created_at")
            applied_at = app_meta.get("applied_at")

            resume_path = app_meta.get("resume")
            has_resume = check_resume_exists(resume_path)

            summaries.append(
                ApplicationSummary(
                    job_id=job_id,
                    company=job.get("company", "Unknown"),
                    title=job.get("title", "Unknown"),
                    location=job.get("location"),
                    match_score=job.get("match_score"),
                    recommendation=job.get("recommendation"),
                    application_status=status,
                    has_resume=has_resume,
                    created_at=created_at,
                    applied_at=applied_at,
                )
            )
        except (json.JSONDecodeError, OSError):
            continue

    # Sort newest first
    summaries.sort(key=lambda item: item.created_at or "", reverse=True)
    return summaries


@router.get("/{job_id}", response_model=ApplicationDetail)
def get_application_detail(job_id: int):
    """Fetch complete application details for a specific job."""
    app_file = APPLICATIONS_DIR / f"job_{job_id}.json"

    if not app_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Application package for job {job_id} not found",
        )

    try:
        with open(app_file, "r", encoding="utf-8") as f:
            pkg = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read application file: {str(e)}",
        )

    job = pkg.get("job", {})
    app_meta = pkg.get("application", {})
    candidate = pkg.get("candidate", {})

    status = app_meta.get("status", "unknown")
    resume_path = app_meta.get("resume")
    resume_exists = check_resume_exists(resume_path)

    # Resolved answers: merge answers dict and candidate info if present
    resolved_answers = app_meta.get("answers", {})
    if not resolved_answers and isinstance(candidate, dict):
        resolved_answers = candidate

    # Verification and automation status
    verification_meta = pkg.get("verification", {})
    verification_passed = verification_meta.get("passed")
    if verification_passed is True:
        verification_status = "passed"
    elif verification_passed is False:
        verification_status = "failed"
    else:
        verification_status = "not_run"

    verification_checks = verification_meta.get("checks", [])

    submission_state = "submitted" if status == "applied" else "pending"
    automation_status = "completed" if status == "applied" else "idle"

    return ApplicationDetail(
        job_id=job.get("id", job_id),
        company=job.get("company", "Unknown"),
        role=job.get("title", "Unknown"),
        location=job.get("location"),
        match_score=job.get("match_score"),
        recommendation=job.get("recommendation"),
        job_url=job.get("url", ""),
        job_description=job.get("description"),
        application_status=status,
        resume_path=resume_path,
        resume_exists=resume_exists,
        resolved_answers=resolved_answers,
        automation_status=automation_status,
        verification_status=verification_status,
        verification_checks=verification_checks,
        submission_state=submission_state,
        created_at=app_meta.get("created_at"),
        applied_at=app_meta.get("applied_at"),
    )
