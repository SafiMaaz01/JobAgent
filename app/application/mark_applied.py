import json
import sys
from datetime import datetime
from pathlib import Path

from app.database.db import get_connection, initialize_database


APPLICATIONS_DIR = Path("data/applications")


def get_ready_applications():
    candidates = []

    if not APPLICATIONS_DIR.exists():
        return candidates

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

            candidates.append((file, package))

        except (json.JSONDecodeError, OSError):
            continue

    return candidates


def get_application_by_job_id(job_id):
    application_file = (
        APPLICATIONS_DIR
        / f"job_{job_id}.json"
    )

    if not application_file.exists():
        return None

    try:
        with open(
            application_file,
            "r",
            encoding="utf-8",
        ) as f:
            package = json.load(f)

    except (json.JSONDecodeError, OSError):
        return None

    status = package.get(
        "application",
        {},
    ).get("status")

    if status != "ready_for_review":
        return None

    return (
        application_file,
        package,
    )


def get_job_status(job_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT
            id,
            company,
            title,
            location,
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
        print()
        print(
            "No ready-for-review applications found."
        )
        return None

    valid_candidates = []

    for file, package in candidates:
        job = package.get(
            "job",
            {},
        )

        job_id = job.get("id")

        if job_id is not None:
            row = get_job_status(job_id)

            if row is None:
                print()
                print(
                    f"Skipping {file.name}: "
                    f"job ID {job_id} does not exist "
                    "in the database."
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

            if row["review_status"] != "approved":
                print()
                print(
                    f"Skipping {file.name}: "
                    f"{row['company']} - {row['title']} "
                    f"is not approved "
                    f"(status: {row['review_status']})."
                )
                continue

        valid_candidates.append(
            (file, package)
        )

    if not valid_candidates:
        print()
        print(
            "No approved, unapplied applications found."
        )
        return None

    print()
    print("=" * 70)
    print("READY APPLICATIONS")
    print("=" * 70)
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
            f"    Job ID: "
            f"{job.get('id', 'Unknown')}"
        )

        print(
            f"    Location: "
            f"{job.get('location', 'Unknown')}"
        )

        print(
            f"    Package: {file.name}"
        )

        print()

    while True:
        choice = input(
            "Select application number "
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


def mark_application_applied(
    application_file,
    package,
):
    application = package.setdefault(
        "application",
        {},
    )

    job = package.get(
        "job",
        {},
    )

    job_id = job.get("id")

    if job_id is None:
        print()
        print(
            "SAFETY CHECK FAILED"
        )
        print()
        print(
            "Application package does not "
            "contain a job ID."
        )
        print(
            "Nothing was changed."
        )
        return False

    row = get_job_status(job_id)

    if row is None:
        print()
        print(
            "SAFETY CHECK FAILED"
        )
        print()
        print(
            f"Job ID {job_id} does not exist "
            "in the database."
        )
        print(
            "Nothing was changed."
        )
        return False

    if row["review_status"] == "applied":
        print()
        print(
            "SAFETY CHECK FAILED"
        )
        print()
        print(
            "This job is already marked as applied."
        )
        print(
            "Nothing was changed."
        )
        return False

    if row["review_status"] != "approved":
        print()
        print(
            "SAFETY CHECK FAILED"
        )
        print()
        print(
            f"This job is not approved. "
            f"Current database status: "
            f"{row['review_status']}"
        )
        print(
            "Only approved jobs can be marked as applied."
        )
        print(
            "Nothing was changed."
        )
        return False

    if application.get("status") != "ready_for_review":
        print()
        print(
            "SAFETY CHECK FAILED"
        )
        print()
        print(
            "Application package is not "
            "ready_for_review."
        )
        print(
            f"Current package status: "
            f"{application.get('status')}"
        )
        print(
            "Nothing was changed."
        )
        return False

    print()
    print("=" * 70)
    print("JOBAGENT - MARK APPLICATION")
    print("=" * 70)

    print()
    print("APPLICATION")
    print("-" * 70)

    print(
        f"Company:     "
        f"{job.get('company', '')}"
    )

    print(
        f"Title:       "
        f"{job.get('title', '')}"
    )

    print(
        f"Location:    "
        f"{job.get('location', '')}"
    )

    print(
        f"Job ID:      "
        f"{job_id}"
    )

    print(
        f"Package:     "
        f"{application_file}"
    )

    print(
        f"Database status: "
        f"{row['review_status']}"
    )

    print(
        f"Package status:  "
        f"{application.get('status', '')}"
    )

    print()
    print("IMPORTANT")
    print("-" * 70)

    print(
        "Only use this command AFTER the "
        "application has actually been submitted."
    )

    print(
        "This command does NOT submit anything."
    )

    print()

    confirmation = input(
        "Did you submit this application? [y/N]: "
    ).strip().lower()

    if confirmation != "y":
        print()
        print(
            "Application was NOT marked as applied."
        )

        print(
            "Nothing was changed."
        )

        return False

    timestamp = datetime.now().isoformat(
        timespec="seconds"
    )

    application["status"] = "applied"
    application["applied_at"] = timestamp

    with open(
        application_file,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            package,
            f,
            indent=2,
            ensure_ascii=False,
        )

    connection = get_connection()

    connection.execute(
        """
        UPDATE jobs
        SET
            review_status = 'applied',
            applied_at = ?
        WHERE id = ?
          AND review_status = 'approved'
        """,
        (
            timestamp,
            job_id,
        ),
    )

    connection.commit()
    connection.close()

    print()
    print("=" * 70)
    print("APPLICATION MARKED AS APPLIED")
    print("=" * 70)

    print()
    print(
        f"Status:     "
        f"{application['status']}"
    )

    print(
        f"Applied at: "
        f"{application['applied_at']}"
    )

    print()

    print(
        "The application will no longer be "
        "selected as ready-for-review."
    )

    print()

    return True


def main():
    initialize_database()

    if len(sys.argv) > 1:
        try:
            job_id = int(
                sys.argv[1]
            )
        except ValueError:
            print(
                "Job ID must be an integer."
            )
            return

        result = get_application_by_job_id(
            job_id
        )

        if result is None:
            print()
            print(
                f"No ready-for-review application "
                f"found for job ID {job_id}."
            )
            return

        application_file, package = result

    else:
        result = select_application()

        if result is None:
            print()
            print(
                "Application selection cancelled."
            )
            return

        application_file, package = result

    mark_application_applied(
        application_file,
        package,
    )


if __name__ == "__main__":
    main()