import json
import json
from datetime import datetime
from pathlib import Path

from app.database.db import get_connection, initialize_database
from app.browser.autofill_application import main as run_application


APPLICATIONS_DIR = Path("data/applications")


def get_ready_applications():
    if not APPLICATIONS_DIR.exists():
        return []

    candidates = []

    for file in APPLICATIONS_DIR.glob("job_*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                package = json.load(f)

            status = package.get(
                "application",
                {},
            ).get("status")

            if status != "ready_for_review":
                continue

            job = package.get("job", {})
            job_id = job.get("id")

            if job_id is None:
                continue

            candidates.append(
                (file, package)
            )

        except (json.JSONDecodeError, OSError):
            continue

    candidates.sort(
        key=lambda item: item[1]
        .get("application", {})
        .get("created_at", ""),
        reverse=True,
    )

    return candidates


def get_job_status(job_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT
            id,
            company,
            title,
            review_status,
            reviewed_at,
            applied_at
        FROM jobs
        WHERE id = ?
        """,
        (job_id,),
    ).fetchone()

    connection.close()

    return row


def verify_job_is_approved(job_id):
    row = get_job_status(job_id)

    if row is None:
        return False

    return row["review_status"] == "approved"


def verify_job_not_already_applied(job_id):
    row = get_job_status(job_id)

    if row is None:
        return False

    return row["review_status"] != "applied"


def select_application():
    candidates = get_ready_applications()

    if not candidates:
        return None

    valid_candidates = []

    for file, package in candidates:
        job = package.get(
            "job",
            {},
        )

        job_id = job.get("id")

        if job_id is None:
            continue

        row = get_job_status(job_id)

        if row is None:
            print()
            print(
                f"Skipping {file.name}: "
                "job no longer exists in the database."
            )
            continue

        if row["review_status"] == "applied":
            print()
            print(
                f"Skipping {file.name}: "
                f"{row['company']} - {row['title']} "
                "is already marked as applied."
            )
            continue

        valid_candidates.append(
            (file, package)
        )

    if not valid_candidates:
        return None

    print()
    print("=" * 60)
    print("READY APPLICATIONS")
    print("=" * 60)
    print()

    for index, (file, package) in enumerate(
        valid_candidates,
        start=1,
    ):
        job = package.get(
            "job",
            {},
        )

        print(
            f"[{index}] "
            f"{job.get('company', 'Unknown')} - "
            f"{job.get('title', 'Unknown')}"
        )

        print(
            f"    Job ID: {job.get('id', 'Unknown')}"
        )

        print(
            f"    Location: "
            f"{job.get('location', 'Unknown')}"
        )

        print(
            f"    Match score: "
            f"{job.get('match_score', 'Unknown')}"
        )

        print(
            f"    Package: {file.name}"
        )

        print()

    while True:
        choice = input(
            "Select an application number "
            "(or press Enter to cancel): "
        ).strip()

        if not choice:
            return None

        try:
            selected_index = int(choice)
        except ValueError:
            print(
                "Please enter a valid number."
            )
            continue

        if not (
            1
            <= selected_index
            <= len(valid_candidates)
        ):
            print(
                "Invalid application number."
            )
            continue

        return valid_candidates[
            selected_index - 1
        ]


def run():
    print()
    print("=" * 60)
    print("JOBAGENT APPLICATION RUNNER")
    print("=" * 60)

    initialize_database()

    result = select_application()

    if result is None:
        print()
        print(
            "No eligible ready-for-review "
            "application packages found."
        )
        print()
        return

    package_file, package = result

    job = package["job"]
    job_id = job["id"]

    print()
    print("FOUND APPLICATION")
    print(f"Package: {package_file}")
    print(f"Company: {job.get('company')}")
    print(f"Title: {job.get('title')}")
    print(f"Location: {job.get('location')}")
    print(f"Job ID: {job_id}")
    print(
        f"Package status: "
        f"{package['application'].get('status')}"
    )

    # -----------------------------------------------------
    # Database safety checks
    # -----------------------------------------------------

    row = get_job_status(job_id)

    if row is None:
        print()
        print("SAFETY CHECK FAILED")
        print(
            "This job does not exist in the database."
        )
        print(
            "Nothing will be opened or submitted."
        )
        return

    print(
        f"Database status: "
        f"{row['review_status']}"
    )

    if row["review_status"] == "applied":
        print()
        print("SAFETY CHECK FAILED")
        print(
            "This job is already marked as applied."
        )
        print(
            "Nothing will be opened or submitted."
        )
        return

    if row["review_status"] != "approved":
        print()
        print("SAFETY CHECK FAILED")
        print(
            "This job is not currently approved."
        )
        print(
            "Nothing will be opened or submitted."
        )
        return

    # -----------------------------------------------------
    # Final pre-browser safety check
    # -----------------------------------------------------

    if not verify_job_not_already_applied(
        job_id
    ):
        print()
        print("SAFETY CHECK FAILED")
        print(
            "This job is already marked as applied."
        )
        print(
            "Nothing will be opened or submitted."
        )
        return

    print()
    print("Approval check: PASSED")
    print("Duplicate application check: PASSED")
    print()
    print("Starting browser autofill...")
    print(
        "Submission requires explicit human "
        "confirmation."
    )
    print()

    submission_successful = run_application(
        str(package_file)
    )

    if submission_successful is True:
        print()
        print("=" * 60)
        print("SUBMISSION CONFIRMED")
        print("=" * 60)
        print()

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        # -------------------------------------------------
        # Update application package
        # -------------------------------------------------

        package["application"]["status"] = "applied"
        package["application"]["applied_at"] = now

        with open(
            package_file,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                package,
                file,
                indent=2,
                ensure_ascii=False,
            )

        # -------------------------------------------------
        # Update database
        # -------------------------------------------------

        connection = get_connection()

        cursor = connection.execute(
            "UPDATE jobs "
            "SET review_status = 'applied', applied_at = ? "
            "WHERE id = ? AND review_status = 'approved'",
            (
                now,
                job_id,
            ),
        )

        connection.commit()
        connection.close()

        if cursor.rowcount != 1:
            print(
                "WARNING: Browser submission was "
                "confirmed, but the database status "
                "could not be updated safely."
            )
            print(
                "The application package was marked "
                "as applied."
            )
            return

        print(
            "Application package marked as applied."
        )
        print(
            "Database status marked as applied."
        )

    else:
        print()
        print("=" * 60)
        print("APPLICATION NOT MARKED AS APPLIED")
        print("=" * 60)
        print()
        print(
            "The browser workflow did not return a "
            "confirmed successful submission."
        )
        print(
            "Database status remains unchanged."
        )
        print(
            "Application package remains "
            "ready_for_review."
        )

    print()
    print("=" * 60)
    print("APPLICATION RUN COMPLETE")
    print("=" * 60)
    print()


if __name__ == "__main__":
    run()