"""
Applications endpoints for inspecting, preparing, and automating job application packages.

This router manages the authoritative application pipeline:
1. `GET /api/applications`: Lists all prepared application packages from `data/applications/`.
2. `GET /api/applications/eligible-jobs`: Finds approved jobs in SQLite that are ready for package creation.
3. `GET /api/applications/{job_id}`: Retrieves complete package details, candidate profile, and questionnaire answers.
4. `POST /api/applications/{job_id}/prepare`: Generates package JSON using authoritative `app.application.prepare`.
5. `POST /api/applications/{job_id}/autofill`: Triggers authoritative Playwright autofill runner with single concurrency.
6. `GET /api/applications/{job_id}/autofill-status`: Live status tracking for active automation runs.
"""
import json
import sqlite3
import time
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_db
from app.api.schemas.application import (
    ApplicationDetail,
    ApplicationSummary,
    MarkSubmittedResponse,
    PreparePackageResponse,
)
from app.api.schemas.job import JobSummary
from app.application.prepare import (
    RESUME_FILE,
    create_application_package,
    load_answer_bank,
)

router = APIRouter(prefix="/api/applications", tags=["Applications"])

# Directory where application packages are stored as JSON files
APPLICATIONS_DIR = Path("data/applications")


def check_resume_exists(resume_path_str: str | None) -> bool:
    """
    Check if the specified resume file exists on the local filesystem.
    Returns True if present and accessible, False otherwise.
    """
    if not resume_path_str:
        return False
    path = Path(resume_path_str)
    return path.exists()


@router.get("", response_model=List[ApplicationSummary])
def list_applications(db: sqlite3.Connection = Depends(get_db)):
    """List all application packages found in data/applications/."""
    if not APPLICATIONS_DIR.exists():
        return []

    # Map job_id to review_status from DB
    db_jobs = {
        row["id"]: row["review_status"]
        for row in db.execute("SELECT id, review_status FROM jobs").fetchall()
    }

    summaries = []
    for file in APPLICATIONS_DIR.glob("job_*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                pkg = json.load(f)

            job = pkg.get("job", {})
            app_meta = pkg.get("application", {})

            job_id = job.get("id")
            if job_id is None:
                stem = file.stem.split("_")
                if len(stem) == 2 and stem[1].isdigit():
                    job_id = int(stem[1])
                else:
                    continue

            status = app_meta.get("status", "unknown")
            created_at = app_meta.get("created_at")
            applied_at = app_meta.get("applied_at")
            submission_source = app_meta.get("submission_source")

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
                    review_status=db_jobs.get(job_id),
                    application_status=status,
                    has_resume=has_resume,
                    created_at=created_at,
                    applied_at=applied_at,
                    submission_source=submission_source,
                )
            )
        except (json.JSONDecodeError, OSError):
            continue

    summaries.sort(key=lambda item: item.created_at or "", reverse=True)
    return summaries


@router.get("/eligible-jobs", response_model=List[JobSummary])
def list_eligible_jobs_for_preparation(db: sqlite3.Connection = Depends(get_db)):
    """List all approved jobs eligible for application package preparation."""
    rows = db.execute(
        """
        SELECT
            id, source, external_id, company, title, location, url,
            posted_at, updated_at, is_relevant, match_score, recommendation,
            review_status, reviewed_at, applied_at
        FROM jobs
        WHERE review_status = 'approved'
        ORDER BY id DESC
        """
    ).fetchall()

    # Check which ones already have a package
    app_job_ids = set()
    if APPLICATIONS_DIR.exists():
        for file in APPLICATIONS_DIR.glob("job_*.json"):
            try:
                parts = file.stem.split("_")
                if len(parts) == 2 and parts[1].isdigit():
                    app_job_ids.add(int(parts[1]))
            except ValueError:
                continue

    items = []
    for row in rows:
        job_id = row["id"]
        items.append(
            JobSummary(
                id=job_id,
                source=row["source"],
                external_id=row["external_id"],
                company=row["company"],
                title=row["title"],
                location=row["location"],
                url=row["url"],
                posted_at=row["posted_at"],
                updated_at=row["updated_at"],
                is_relevant=row["is_relevant"],
                match_score=row["match_score"],
                recommendation=row["recommendation"],
                review_status=row["review_status"],
                reviewed_at=row["reviewed_at"],
                applied_at=row["applied_at"],
                has_application=(job_id in app_job_ids),
            )
        )
    return items


@router.get("/{job_id}", response_model=ApplicationDetail)
def get_application_detail(job_id: int, db: sqlite3.Connection = Depends(get_db)):
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
    match_meta = pkg.get("match", {})

    status = app_meta.get("status", "unknown")
    resume_path = app_meta.get("resume")
    resume_exists = check_resume_exists(resume_path)

    # Resolved answers: answers dict or candidate QA pairs
    resolved_answers = app_meta.get("answers", {})
    if not resolved_answers and isinstance(candidate, dict):
        # Extract direct QA questions if candidate dictionary has them
        resolved_answers = candidate.get("personal", {})

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

    # Query active automation status
    from app.api.automation import automation_manager
    from app.api.routers.tasks import get_task_state

    active_job_id = automation_manager.get_active_job_id()
    if active_job_id == job_id:
        active_task = get_task_state()
        automation_status = active_task.get("status", "running")
        if active_task.get("details", {}).get("verification_passed"):
            verification_status = "passed"
    else:
        automation_status = "completed" if status == "applied" else "idle"

    # Query review_status and applied_at from DB
    row = db.execute("SELECT review_status, applied_at FROM jobs WHERE id = ?", (job_id,)).fetchone()
    db_review_status = row["review_status"] if row else None
    db_applied_at = row["applied_at"] if row else None

    if db_review_status == "applied":
        status = "applied"

    submission_state = "submitted" if status == "applied" else "pending"
    applied_at = app_meta.get("applied_at") or db_applied_at
    submission_source = app_meta.get("submission_source")

    return ApplicationDetail(
        job_id=job.get("id", job_id),
        company=job.get("company", "Unknown"),
        role=job.get("title", "Unknown"),
        location=job.get("location"),
        match_score=job.get("match_score"),
        recommendation=job.get("recommendation"),
        review_status=db_review_status,
        job_url=job.get("url", ""),
        job_description=job.get("description"),
        application_status=status,
        resume_path=resume_path,
        resume_exists=resume_exists,
        resolved_answers=resolved_answers,
        candidate=candidate if isinstance(candidate, dict) else None,
        match_details=match_meta.get("details"),
        automation_status=automation_status,
        verification_status=verification_status,
        verification_checks=verification_checks,
        submission_state=submission_state,
        created_at=app_meta.get("created_at"),
        applied_at=applied_at,
        submission_source=submission_source,
    )


@router.post("/{job_id}/prepare", response_model=PreparePackageResponse)
def prepare_application_package(job_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Prepare an application package for an approved job using app.application.prepare."""
    # 1. Verify job exists
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    # 2. Strict safety check: must be approved
    if job["review_status"] != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Job #{job_id} ({job['company']}) has status '{job['review_status']}'. Only approved jobs can be prepared.",
        )

    # 3. Verify resume exists
    if not RESUME_FILE.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Resume file not found at {RESUME_FILE}. Please ensure resume.pdf exists.",
        )

    try:
        answer_bank = load_answer_bank()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load answer bank: {str(e)}",
        )

    # 4. Delegate to authoritative existing function
    try:
        output_file = create_application_package(job, answer_bank)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create application package: {str(e)}",
        )

    return PreparePackageResponse(
        job_id=job_id,
        status="ready_for_review",
        message=f"Application package successfully prepared for {job['company']} - {job['title']}",
        package_file=str(output_file),
    )


@router.post("/{job_id}/autofill")
def run_application_autofill(job_id: int, db: sqlite3.Connection = Depends(get_db)):
    """
    Launch authoritative browser autofill for an approved and prepared application.
    Enforces validation, duplicate protection, and human confirmation gate.
    """
    from app.api.automation import automation_manager

    # 1. Verify job exists in database
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    # 2. Strict safety check: must be approved
    if job["review_status"] != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot run automation: Job #{job_id} review status is '{job['review_status']}'. Only approved jobs can be autofilled.",
        )
    # 2b. Guard against already submitted applications
    if job["review_status"] == "applied":
        raise HTTPException(
            status_code=400,
            detail=f"Job #{job_id} has already been submitted (review_status='applied').",
        )

    # 3. Verify package file exists
    package_file = APPLICATIONS_DIR / f"job_{job_id}.json"
    if not package_file.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Application package for Job #{job_id} has not been prepared yet. Please prepare the package first.",
        )

    # 4. Check application package status
    try:
        with open(package_file, "r", encoding="utf-8") as f:
            pkg_data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read application package: {str(e)}")

    pkg_status = pkg_data.get("application", {}).get("status")
    if pkg_status == "applied":
        raise HTTPException(
            status_code=400,
            detail=f"Application for Job #{job_id} has already been submitted (status: applied).",
        )

    # 5. Start or return existing automation run
    result = automation_manager.start_autofill(job_id=job_id, package_path=package_file, job_info=dict(job))
    return result


@router.get("/{job_id}/autofill-status")
def get_application_autofill_status(job_id: int):
    """Retrieve live automation and verification status for a specific application."""
    from app.api.automation import automation_manager
    from app.api.routers.tasks import get_task_state

    active_job_id = automation_manager.get_active_job_id()
    if active_job_id == job_id:
        task_state = get_task_state()
        return {
            "is_active": True,
            "status": task_state.get("status", "running"),
            "message": task_state.get("message"),
            "progress": task_state.get("progress", 0),
            "details": task_state.get("details"),
        }

    # Check if package exists and its status
    package_file = APPLICATIONS_DIR / f"job_{job_id}.json"
    if package_file.exists():
        try:
            with open(package_file, "r", encoding="utf-8") as f:
                pkg_data = json.load(f)
            pkg_status = pkg_data.get("application", {}).get("status", "unknown")
            return {
                "is_active": False,
                "status": pkg_status,
                "message": f"Package status: {pkg_status}",
                "progress": 100 if pkg_status == "applied" else 0,
                "details": None,
            }
        except Exception:
            pass

    return {
        "is_active": False,
        "status": "idle",
        "message": "No automation run recorded for this job",
        "progress": 0,
        "details": None,
    }


@router.post("/{job_id}/mark-submitted", response_model=MarkSubmittedResponse)
def mark_application_as_submitted(job_id: int, db: sqlite3.Connection = Depends(get_db)):
    """
    Explicitly mark an application as submitted externally by human user.
    Safely cancels any active automation runner for this job and authoritatively updates SQLite + package JSON.
    """
    # 1. Verify job exists
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    app_file = APPLICATIONS_DIR / f"job_{job_id}.json"

    # Check current DB & package status for idempotency
    existing_db_review_status = job["review_status"]
    existing_applied_at = job["applied_at"]

    existing_pkg = None
    if app_file.exists():
        try:
            with open(app_file, "r", encoding="utf-8") as f:
                existing_pkg = json.load(f)
        except Exception:
            pass

    pkg_app_meta = existing_pkg.get("application", {}) if existing_pkg else {}
    pkg_status = pkg_app_meta.get("status")
    pkg_applied_at = pkg_app_meta.get("applied_at") or existing_applied_at
    pkg_source = pkg_app_meta.get("submission_source") or ("manual" if existing_db_review_status == "applied" else None)

    # 2. Idempotency check: if already applied
    if existing_db_review_status == "applied" or pkg_status == "applied":
        return MarkSubmittedResponse(
            job_id=job_id,
            application_status="applied",
            review_status="applied",
            applied_at=pkg_applied_at or existing_applied_at,
            submission_source=pkg_source or "manual",
            message=f"Application for Job #{job_id} is already marked as submitted.",
            already_submitted=True,
        )

    # 3. Handle active automation safely
    from app.api.automation import automation_manager

    active_job_id = automation_manager.get_active_job_id()
    was_automation_active = (active_job_id == job_id)
    if was_automation_active:
        automation_manager.cancel()

    # 4. Authoritative Database update
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    db.execute(
        """
        UPDATE jobs
        SET review_status = 'applied',
            applied_at = ?
        WHERE id = ?
        """,
        (timestamp, job_id),
    )
    db.commit()

    # 5. Application Package JSON update
    if existing_pkg is not None:
        existing_pkg.setdefault("application", {})["status"] = "applied"
        existing_pkg["application"]["applied_at"] = timestamp
        existing_pkg["application"]["submission_source"] = "manual"
        try:
            with open(app_file, "w", encoding="utf-8") as f:
                json.dump(existing_pkg, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    msg = (
        f"Automation cancelled and application for {job['company']} marked as submitted manually."
        if was_automation_active
        else f"Application for {job['company']} marked as submitted manually."
    )

    return MarkSubmittedResponse(
        job_id=job_id,
        application_status="applied",
        review_status="applied",
        applied_at=timestamp,
        submission_source="manual",
        message=msg,
        already_submitted=False,
    )
