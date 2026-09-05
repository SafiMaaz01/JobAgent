import json
from pathlib import Path

from app.database.db import get_connection, initialize_database
from app.browser.test_browser import run_application


APPLICATIONS_DIR = Path("data/applications")


def get_latest_ready_application():
    if not APPLICATIONS_DIR.exists():
        return None

    candidates = []

    for file in APPLICATIONS_DIR.glob("job_*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                package = json.load(f)

            status = package.get("application", {}).get("status")

            if status != "ready_for_review":
                continue

            job = package.get("job", {})
            job_id = job.get("id")

            if job_id is None:
                continue

            candidates.append((file, package))

        except (json.JSONDecodeError, OSError):
            continue

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[1]
        .get("application", {})
        .get("created_at", ""),
        reverse=True,
    )

    return candidates[0]


def verify_job_is_approved(job_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT
            id,
            company,
            title,
            review_status
        FROM jobs
        WHERE id = ?
        """,
        (job_id,),
    ).fetchone()

    connection.close()

    if row is None:
        return False

    return row["review_status"] == "approved"


def run():
    print()
    print("=" * 60)
    print("JOBAGENT APPLICATION RUNNER")
    print("=" * 60)

    initialize_database()

    result = get_latest_ready_application()

    if result is None:
        print()
        print("No ready-for-review application packages found.")
        print()
        print("Run the approval step first, then prepare the application.")
        return

    package_file, package = result

    job = package["job"]

    print()
    print("FOUND APPLICATION")
    print(f"Package: {package_file}")
    print(f"Company: {job.get('company')}")
    print(f"Title: {job.get('title')}")
    print(f"Location: {job.get('location')}")
    print(f"Job ID: {job.get('id')}")
    print(f"Status: {package['application'].get('status')}")

    if not verify_job_is_approved(job["id"]):
        print()
        print("SAFETY CHECK FAILED")
        print("This job is not currently approved.")
        print("Nothing will be opened or submitted.")
        return

    print()
    print("Approval check: PASSED")
    print()
    print("Starting browser autofill...")
    print("The Submit Application button will NOT be clicked.")
    print()

    run_application(str(package_file))

    print()
    print("=" * 60)
    print("APPLICATION RUN COMPLETE")
    print("=" * 60)
    print()
    print("Browser remains open for manual review.")
    print("Nothing was submitted.")


if __name__ == "__main__":
    run()