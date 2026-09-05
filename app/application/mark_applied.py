import json
from datetime import datetime
from pathlib import Path

from app.database.db import get_connection, initialize_database


APPLICATIONS_DIR = Path("data/applications")


def get_latest_ready_application():
    candidates = []

    if not APPLICATIONS_DIR.exists():
        return None

    for file in APPLICATIONS_DIR.glob("job_*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                package = json.load(f)

            status = package.get("application", {}).get("status")

            if status != "ready_for_review":
                continue

            created_at = package.get(
                "application", {}
            ).get("created_at", "")

            candidates.append(
                (created_at, file, package)
            )

        except (json.JSONDecodeError, OSError):
            continue

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return candidates[0]


def mark_application_applied():
    initialize_database()

    result = get_latest_ready_application()

    if result is None:
        print()
        print("No ready-for-review application found.")
        return

    created_at, package_file, package = result

    job = package.get("job", {})
    application = package.setdefault(
        "application",
        {},
    )

    print()
    print("=" * 70)
    print("JOBAGENT - MARK APPLICATION")
    print("=" * 70)

    print()
    print("APPLICATION")
    print("-" * 70)
    print(f"Company:     {job.get('company', '')}")
    print(f"Title:       {job.get('title', '')}")
    print(f"Location:    {job.get('location', '')}")
    print(f"Job ID:      {job.get('id', '')}")
    print(f"Package:     {package_file}")
    print(
        f"Current status: "
        f"{application.get('status', '')}"
    )

    print()
    print("IMPORTANT")
    print("-" * 70)
    print(
        "Only use this command AFTER you have manually "
        "reviewed and submitted the application."
    )
    print()
    print(
        "This command does NOT submit anything."
    )

    print()

    confirmation = input(
        "Did you manually submit this application? [y/N]: "
    ).strip().lower()

    if confirmation != "y":
        print()
        print("Application was NOT marked as applied.")
        print("Nothing was changed.")
        return

    timestamp = datetime.now().isoformat(
        timespec="seconds"
    )

    application["status"] = "applied"
    application["applied_at"] = timestamp

    with open(
        package_file,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            package,
            f,
            indent=2,
            ensure_ascii=False,
        )

    job_id = job.get("id")

    if job_id is not None:
        connection = get_connection()

        connection.execute(
            """
            UPDATE jobs
            SET review_status = 'applied',
                applied_at = ?
            WHERE id = ?
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
    print(f"Status:     {application['status']}")
    print(f"Applied at: {application['applied_at']}")
    print()
    print(
        "The application will no longer be selected "
        "as ready-for-review."
    )
    print()
    print(
        "Nothing was submitted by JobAgent."
    )


if __name__ == "__main__":
    mark_application_applied()