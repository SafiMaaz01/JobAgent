import sqlite3
from datetime import datetime
from app.database.db import get_connection, initialize_database


def get_jobs_for_review():
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


def update_review_status(job_id, status):
    connection = get_connection()

    connection.execute(
        """
        UPDATE jobs
        SET review_status = ?,
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


def display_job(job, number, total):
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
    print(f"URL:            {job['url']}")
    print()
    print("Description:")
    print("-" * 80)

    description = job["description"] or ""

    # Keep the terminal readable.
    if len(description) > 3000:
        description = description[:3000] + "\n...[description truncated]"

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
            choice = input("Your decision [A/R/S/Q]: ").strip().lower()

            if choice == "a":
                update_review_status(job["id"], "approved")
                print("Approved.")
                break

            if choice == "r":
                update_review_status(job["id"], "rejected")
                print("Rejected.")
                break

            if choice == "s":
                print("Skipped. This job remains pending.")
                break

            if choice == "q":
                print()
                print("Review stopped.")
                return

            print("Invalid choice. Please enter A, R, S, or Q.")

    print()
    print("=" * 80)
    print("REVIEW COMPLETE")
    print("=" * 80)
    print()


if __name__ == "__main__":
    review_jobs()