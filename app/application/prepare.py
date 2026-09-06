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
            recommendation,
            match_details,
            review_status,
            reviewed_at
        FROM jobs
        WHERE review_status = 'approved'
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()
    return jobs


def parse_match_details(raw_details):
    if not raw_details:
        return {}

    try:
        details = json.loads(raw_details)

        if isinstance(details, dict):
            return details

    except (json.JSONDecodeError, TypeError):
        pass

    return {}


def create_application_package(job, answer_bank):
    APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat(timespec="seconds")

    match_details = parse_match_details(
        job["match_details"]
    )

    package = {
        "job": {
            "id": job["id"],
            "company": job["company"],
            "title": job["title"],
            "location": job["location"],
            "url": job["url"],
            "description": job["description"],
            "match_score": job["match_score"],
            "recommendation": job["recommendation"],
        },
        "match": {
            "score": job["match_score"],
            "recommendation": job["recommendation"],
            "details": match_details,
        },
        "candidate": answer_bank,
        "application": {
            "status": "ready_for_review",
            "created_at": timestamp,
            "resume": str(RESUME_FILE),
            "cover_letter": None,
            "answers": {},
            "answer_policy": {
                "unknown_information": "ASK_USER",
                "never_invent_experience": True,
                "never_invent_qualifications": True,
                "never_guess_legal_or_work_authorization_answers": True,
            },
        },
    }

    filename = f"job_{job['id']}.json"
    output_file = APPLICATIONS_DIR / filename

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            package,
            file,
            indent=2,
            ensure_ascii=False,
        )

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

    prepared_count = 0

    for job in jobs:
        print(
            f"Preparing: "
            f"{job['company']} — {job['title']}"
        )

        output_file = create_application_package(
            job,
            answer_bank,
        )

        prepared_count += 1

        print(f"Created: {output_file}")
        print()

    print("=" * 80)
    print("APPLICATION PREPARATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Packages created: {prepared_count}")
    print()


if __name__ == "__main__":
    prepare_applications()