"""
Jobs endpoints for querying, filtering, inspecting, and reviewing jobs.

This router provides:
1. `GET /api/jobs`: Paginated search, sorting, and multi-criteria filtering over SQLite `jobs`.
2. `GET /api/jobs/review/queue`: Fetches pending jobs eligible for review using authoritative `app.approval.review`.
3. `POST /api/jobs/{id}/review`: Approves or rejects a job, updating review timestamps and state.
4. `GET /api/jobs/{id}`: Detailed view including raw descriptions and AI match breakdown.
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_db
from app.api.schemas.job import (
    JobDetail,
    JobListResponse,
    JobSummary,
    ReviewRequest,
    ReviewResponse,
)
from app.approval.review import get_jobs_for_review, update_review_status

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

# Directory where prepared application packages reside
APPLICATIONS_DIR = Path("data/applications")


def parse_match_details_json(raw: Optional[str]) -> Optional[dict]:
    """
    Parse JSON match details string safely into a dict.
    Returns None if empty or if invalid JSON formatting is encountered.
    """
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def get_application_info_for_job(job_id: int) -> tuple[bool, Optional[str]]:
    """Check if an application package exists for the job and return status."""
    app_file = APPLICATIONS_DIR / f"job_{job_id}.json"
    if not app_file.exists():
        return False, None
    try:
        with open(app_file, "r", encoding="utf-8") as f:
            pkg = json.load(f)
            status = pkg.get("application", {}).get("status")
            return True, status
    except (json.JSONDecodeError, OSError):
        return True, None


@router.get("", response_model=JobListResponse)
def list_jobs(
    status: Optional[str] = Query(None, description="Filter by review status: pending, approved, applied, rejected, all"),
    recommendation: Optional[str] = Query(None, description="Filter by recommendation: APPLY, SKIP, all"),
    is_relevant: Optional[int] = Query(None, description="Filter by relevance: 1 or 0"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum match score"),
    search: Optional[str] = Query(None, description="Search term matching company or title"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Page size limit"),
    sort_by: str = Query("match_score", description="Sort field: match_score, id, company, title, posted_at"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    db: sqlite3.Connection = Depends(get_db),
):
    """Query jobs with rich filtering, search, and pagination."""
    where_clauses = []
    params = []

    if status and status.lower() != "all":
        where_clauses.append("review_status = ?")
        params.append(status.lower())

    if recommendation and recommendation.upper() != "ALL":
        where_clauses.append("recommendation = ?")
        params.append(recommendation.upper())

    if is_relevant is not None:
        where_clauses.append("is_relevant = ?")
        params.append(is_relevant)

    if min_score is not None:
        where_clauses.append("match_score >= ?")
        params.append(min_score)

    if search:
        search_pattern = f"%{search.strip()}%"
        where_clauses.append("(company LIKE ? OR title LIKE ?)")
        params.extend([search_pattern, search_pattern])

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Count total matching rows
    count_sql = f"SELECT COUNT(*) FROM jobs {where_sql}"
    total = db.execute(count_sql, params).fetchone()[0]

    # Validate sorting
    allowed_sort_fields = {
        "match_score": "match_score",
        "id": "id",
        "company": "company",
        "title": "title",
        "posted_at": "posted_at",
        "reviewed_at": "reviewed_at",
    }
    sort_field = allowed_sort_fields.get(sort_by, "match_score")
    order = "ASC" if sort_order.lower() == "asc" else "DESC"

    offset = (page - 1) * limit

    # Use NULLS LAST for match_score when sorting descending
    if sort_field == "match_score" and order == "DESC":
        order_sql = "ORDER BY match_score IS NULL, match_score DESC, id DESC"
    else:
        order_sql = f"ORDER BY {sort_field} {order}, id DESC"

    query_sql = f"""
        SELECT
            id, source, external_id, company, title, location, url,
            posted_at, updated_at, is_relevant, match_score, recommendation,
            review_status, reviewed_at, applied_at
        FROM jobs
        {where_sql}
        {order_sql}
        LIMIT ? OFFSET ?
    """

    rows = db.execute(query_sql, params + [limit, offset]).fetchall()

    # Pre-check application files to avoid repeated disk reads
    app_job_ids = set()
    if APPLICATIONS_DIR.exists():
        for file in APPLICATIONS_DIR.glob("job_*.json"):
            try:
                name = file.stem  # e.g. job_474
                parts = name.split("_")
                if len(parts) == 2 and parts[1].isdigit():
                    app_job_ids.add(int(parts[1]))
            except ValueError:
                continue

    items = []
    for row in rows:
        job_id = row["id"]
        item = JobSummary(
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
        items.append(item)

    pages = (total + limit - 1) // limit if limit > 0 else 0

    return JobListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/review/queue", response_model=List[JobDetail])
def get_review_queue_jobs():
    """Fetch all pending jobs eligible for human review using existing review.py rules."""
    rows = get_jobs_for_review()
    items = []
    for row in rows:
        job_id = row["id"]
        parsed_match = parse_match_details_json(row["match_details"])
        has_app, app_status = get_application_info_for_job(job_id)
        items.append(
            JobDetail(
                id=job_id,
                source="greenhouse",
                external_id=str(job_id),
                company=row["company"],
                title=row["title"],
                location=row["location"],
                url=row["url"],
                description=row["description"],
                is_relevant=1,
                match_score=row["match_score"],
                recommendation=row["recommendation"],
                match_details=parsed_match,
                review_status="pending",
                has_application=has_app,
                application_status=app_status,
            )
        )
    return items


@router.get("/{job_id}", response_model=JobDetail)
def get_job_detail(job_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Fetch full job details including description, parsed match details, and application state."""
    row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    parsed_match = parse_match_details_json(row["match_details"])
    has_app, app_status = get_application_info_for_job(job_id)

    return JobDetail(
        id=row["id"],
        source=row["source"],
        external_id=row["external_id"],
        company=row["company"],
        title=row["title"],
        location=row["location"],
        url=row["url"],
        description=row["description"],
        posted_at=row["posted_at"],
        updated_at=row["updated_at"],
        is_relevant=row["is_relevant"],
        match_score=row["match_score"],
        recommendation=row["recommendation"],
        matched_at=row["matched_at"],
        match_details=parsed_match,
        review_status=row["review_status"],
        reviewed_at=row["reviewed_at"],
        applied_at=row["applied_at"],
        has_application=has_app,
        application_status=app_status,
    )


@router.post("/{job_id}/review", response_model=ReviewResponse)
def review_job(job_id: int, payload: ReviewRequest, db: sqlite3.Connection = Depends(get_db)):
    """Submit an approve or reject decision for a job delegating to existing update_review_status logic."""
    status = payload.status.strip().lower()
    if status not in ("approved", "rejected", "pending"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid review status: '{payload.status}'. Allowed: approved, rejected, pending",
        )

    row = db.execute("SELECT id, company, title FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    # Call authoritative update logic from existing app.approval.review module
    update_review_status(job_id, status)

    updated = db.execute("SELECT review_status, reviewed_at FROM jobs WHERE id = ?", (job_id,)).fetchone()

    return ReviewResponse(
        id=job_id,
        review_status=updated["review_status"],
        reviewed_at=updated["reviewed_at"],
        message=f"Job #{job_id} ({row['company']} - {row['title']}) marked as {status}.",
    )


