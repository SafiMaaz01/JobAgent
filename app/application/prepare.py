import json
from datetime import datetime
from pathlib import Path

from app.database.db import get_connection, initialize_database

APPLICATIONS_DIR = Path("data/applications")
RESUME_FILE = Path("data/resume/resume.pdf")
ANSWERS_FILE = Path("data/application_answers.json")


def load_answer_bank():
    with open(ANSWERS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_approved_jobs():
    connection = get_connection()
    jobs = connection.execute(
        """
        SELECT
            id,
            company,
            title,
            location,
            url,
            description,
            match_score,
            recommendation
        FROM jobs
        WHERE review_status = 'approved'
        ORDER BY id DESC
        """
    ).fetchall()
    connection.close()
    return jobs


def create_application_package(job, answer_bank):
    APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat(timespec="seconds")

    package = {
        "job": {
            "id": job["id"],
            "company": job["company"],
            "title": job["title"],
            "location": job["location"],
            "url": job["url"],
            "match_score": job["match_score"],
            "recommendation": job["recommendation"],
        },
        "candidate": answer_bank,
        "application": {
            "status": "ready_for_review",
            "created_at": timestamp,
            "resume": str(RESUME_FILE),
            "cover_letter": None,
            "answers": {},
        },
    }

    filename = f"job_{job['id']}.json"
    output_file = APPLICATIONS_DIR / filename

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(package, file, indent=2, ensure_ascii=False)

    return output_file


def prepare_applications():
    initialize_database()

    if not RESUME_FILE.exists():
        print()
        print("=" * 80)
        print("RESUME NOT FOUND")
        print("=" * 80)
        print()
        print(f"Expected resume: {RESUME_FILE}")
        print()
        return

    if not ANSWERS_FILE.exists():
        print()
        print("=" * 80)
        print("ANSWER BANK NOT FOUND")
        print("=" * 80)
        print()
        print(f"Expected answer bank: {ANSWERS_FILE}")
        print()
        return

    answer_bank = load_answer_bank()

    jobs = get_approved_jobs()

    if not jobs:
        print()
        print("=" * 80)
        print("NO APPROVED JOBS")
        print("=" * 80)
        print()
        print("Approve a job first using:")
        print("python -m app.approval.review")
        print()
        return

    print()
    print("=" * 80)
    print("APPLICATION PREPARATION")
    print("=" * 80)
    print()

    for job in jobs:
        print(f"Preparing: {job['company']} — {job['title']}")

        output_file = create_application_package(
            job,
            answer_bank,
        )

        print(f"Created: {output_file}")
        print()

    print("=" * 80)
    print("APPLICATION PREPARATION COMPLETE")
    print("=" * 80)
    print()


if __name__ == "__main__":
    prepare_applications()