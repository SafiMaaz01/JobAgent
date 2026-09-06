"""Dashboard statistics endpoint."""
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, Depends
from app.api.deps import get_db

router = APIRouter(prefix="/api/stats", tags=["Stats"])

APPLICATIONS_DIR = Path("data/applications")


@router.get("", response_model=Dict[str, Any])
def get_dashboard_stats(db: sqlite3.Connection = Depends(get_db)):
    """Return live dashboard statistics computed from database and application files."""
    total_jobs = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    relevant_jobs = db.execute("SELECT COUNT(*) FROM jobs WHERE is_relevant = 1").fetchone()[0]

    pending_review = db.execute(
        """
        SELECT COUNT(*)
        FROM jobs
        WHERE is_relevant = 1
          AND recommendation = 'APPLY'
          AND review_status = 'pending'
        """
    ).fetchone()[0]

    approved = db.execute("SELECT COUNT(*) FROM jobs WHERE review_status = 'approved'").fetchone()[0]
    applied = db.execute("SELECT COUNT(*) FROM jobs WHERE review_status = 'applied'").fetchone()[0]
    rejected = db.execute("SELECT COUNT(*) FROM jobs WHERE review_status = 'rejected'").fetchone()[0]

    avg_score_row = db.execute(
        """
        SELECT ROUND(AVG(match_score), 1)
        FROM jobs
        WHERE is_relevant = 1
          AND match_score IS NOT NULL
        """
    ).fetchone()[0]

    avg_match_score = float(avg_score_row) if avg_score_row is not None else 0.0

    # Applications packages stats
    ready_applications = 0
    total_application_packages = 0
    if APPLICATIONS_DIR.exists():
        for file in APPLICATIONS_DIR.glob("job_*.json"):
            total_application_packages += 1
            try:
                with open(file, "r", encoding="utf-8") as f:
                    pkg = json.load(f)
                    if pkg.get("application", {}).get("status") == "ready_for_review":
                        ready_applications += 1
            except (json.JSONDecodeError, OSError):
                continue

    return {
        "total_jobs": total_jobs,
        "relevant_jobs": relevant_jobs,
        "pending_review": pending_review,
        "approved": approved,
        "applied": applied,
        "rejected": rejected,
        "ready_applications": ready_applications,
        "total_application_packages": total_application_packages,
        "avg_match_score": avg_match_score,
    }
