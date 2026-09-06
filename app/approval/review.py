"""Human review and approval workflow for matched jobs.

This module retrieves jobs recommended for application by the AI matcher
(is_relevant=1, recommendation='APPLY', review_status='pending') and updates their
status to 'approved' or 'rejected'. It powers both the interactive CLI review tool
and the Next.js Review Queue API.
"""
import json
from datetime import datetime

from app.database.db import get_connection, initialize_database


def get_jobs_for_review():
    """
    Fetch all relevant jobs that have recommendation='APPLY' and review_status='pending'.
    
    Ordered by match_score descending so highest priority opportunities appear first.
    """
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            company,
            title,
            location,
            url,
            match_score,
            recommendation,
            match_details,
            description
        FROM jobs
        WHERE is_relevant = 1
          AND recommendation = 'APPLY'
          AND review_status = 'pending'
        ORDER BY match_score DESC, id DESC
        """
    ).fetchall()

    connection.close()

    return rows


def update_review_status(job_id: int, status: str):
    """
    Persist human review status decision ('approved' or 'rejected') and record timestamp.
    """
    connection = get_connection()

    connection.execute(
        """
        UPDATE jobs
        SET
            review_status = ?,
            reviewed_at = ?
        WHERE id = ?
        """,
        (
            status,
            datetime.now().isoformat(timespec="seconds"),
            job_id,
        ),
    )

    connection.commit()
    connection.close()


def parse_match_details(job):
    """
    Safely parse the JSON match_details column from a job record.
    """
    raw_details = job["match_details"]

    if not raw_details:

        return {}

    try:
        details = json.loads(raw_details)

        if isinstance(details, dict):
            return details

    except (json.JSONDecodeError, TypeError):
        pass

    return {}


def print_list(title, items):
    if not items:
        return

    print(title)
    print("-" * 80)

    for item in items:
        print(f"  • {item}")

    print()


def display_job(job, number, total):
    match_details = parse_match_details(job)

    print()
    print("=" * 80)
    print(f"JOB {number} OF {total}")
    print("=" * 80)
    print()

    print(f"Company:        {job['company']}")
    print(f"Title:          {job['title']}")
    print(f"Location:       {job['location']}")
    print(f"Match score:    {job['match_score']}")
    print(f"Recommendation: {job['recommendation']}")

    if match_details:
        seniority = match_details.get(
            "seniority_level",
            match_details.get("seniority", "Unknown"),
        )

        employment_type = match_details.get(
            "employment_type",
            "Unknown",
        )

        # Internship is deterministically treated as Intern.
        if employment_type == "Internship":
            seniority = "Intern"

        print(f"Seniority:      {seniority}")
        print(f"Employment:     {employment_type}")
        print(
            f"Location match: "
            f"{match_details.get('location_match', 'Unknown')}"
        )

    print()
    print(f"URL:            {job['url']}")
    print()

    reason = match_details.get("reason")

    if reason:
        print("Why this job matches:")
        print("-" * 80)
        print(reason)
        print()

    print_list(
        "Strong matches:",
        match_details.get("strong_matches", []),
    )

    print_list(
        "Missing preferred qualifications:",
        match_details.get("missing_preferred_qualifications", []),
    )

    print_list(
        "Concerns:",
        match_details.get("concerns", []),
    )

    missing_minimum = match_details.get(
        "missing_minimum_requirements",
        [],
    )

    if missing_minimum:
        print_list(
            "Missing minimum requirements:",
            missing_minimum,
        )

    print("Description:")
    print("-" * 80)

    description = job["description"] or ""

    if len(description) > 3000:
        description = (
            description[:3000]
            + "\n...[description truncated]"
        )

    print(description)

    print("-" * 80)
    print()


def review_jobs():
    initialize_database()

    jobs = get_jobs_for_review()

    if not jobs:
        print()
        print("=" * 80)
        print("NO JOBS WAITING FOR REVIEW")
        print("=" * 80)
        print()
        return

    total = len(jobs)

    print()
    print("=" * 80)
    print("JOB APPROVAL REVIEW")
    print("=" * 80)
    print()

    print(f"Jobs waiting for review: {total}")
    print()

    print("Commands:")
    print("  A = Approve")
    print("  R = Reject")
    print("  S = Skip")
    print("  Q = Quit")
    print()

    for index, job in enumerate(jobs, start=1):
        display_job(job, index, total)

        while True:
            choice = input(
                "Your decision [A/R/S/Q]: "
            ).strip().lower()

            if choice == "a":
                update_review_status(
                    job["id"],
                    "approved",
                )
                print("Approved.")
                break

            if choice == "r":
                update_review_status(
                    job["id"],
                    "rejected",
                )
                print("Rejected.")
                break

            if choice == "s":
                print(
                    "Skipped. "
                    "This job remains pending."
                )
                break

            if choice == "q":
                print()
                print("Review stopped.")
                return

            print(
                "Invalid choice. "
                "Please enter A, R, S, or Q."
            )

    print()
    print("=" * 80)
    print("REVIEW COMPLETE")
    print("=" * 80)
    print()


if __name__ == "__main__":
    review_jobs()