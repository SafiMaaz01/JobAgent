"""Greenhouse Job Collector.

Fetches open roles across target company Greenhouse job boards defined in
data/sources.json, normalizes data models, runs initial deterministic filtering,
and safely inserts or updates records in the SQLite database.
"""
import json
from pathlib import Path

import requests

from app.database.db import get_connection, initialize_database
from app.jobs.filter import is_relevant_job
from app.jobs.normalize import normalize_greenhouse_job


SOURCES_FILE = Path("data/sources.json")


def load_sources():
    """Load target company board tokens from data/sources.json."""
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_greenhouse_jobs(board_token: str):
    """Fetch all open job listings including full descriptions for a Greenhouse board token."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"


    response = requests.get(
        url,
        params={"content": "true"},
        timeout=30,
    )

    response.raise_for_status()

    return response.json()["jobs"]


def save_job(job):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO jobs (
            source,
            external_id,
            company,
            title,
            location,
            url,
            description,
            posted_at,
            updated_at,
            is_relevant
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(source, external_id)
        DO UPDATE SET
            title = excluded.title,
            location = excluded.location,
            url = excluded.url,
            description = excluded.description,
            updated_at = excluded.updated_at,
            is_relevant = excluded.is_relevant
        """,
        (
            job["source"],
            job["external_id"],
            job["company"],
            job["title"],
            job["location"],
            job["url"],
            job["description"],
            job["posted_at"],
            job["updated_at"],
            int(job["is_relevant"]),
        ),
    )

    connection.commit()
    connection.close()


def collect_company(company, board_token):
    print("=" * 80)
    print(f"Collecting jobs from: {company}")
    print(f"Greenhouse board: {board_token}")
    print()

    raw_jobs = get_greenhouse_jobs(board_token)

    relevant_count = 0

    for raw_job in raw_jobs:
        job = normalize_greenhouse_job(
            raw_job,
            company,
        )

        job["is_relevant"] = is_relevant_job(raw_job)

        save_job(job)

        if job["is_relevant"]:
            relevant_count += 1

    print(f"Total jobs: {len(raw_jobs)}")
    print(f"Relevant jobs: {relevant_count}")
    print()

    return len(raw_jobs), relevant_count


def main():
    initialize_database()

    config = load_sources()

    greenhouse_sources = config.get("greenhouse", [])

    if not greenhouse_sources:
        print("No Greenhouse sources configured.")
        return

    total_jobs = 0
    total_relevant = 0
    successful_sources = 0
    failed_sources = 0

    print()
    print("=" * 80)
    print("JOB COLLECTION STARTED")
    print("=" * 80)
    print()

    for source in greenhouse_sources:
        company = source["company"]
        board_token = source["board_token"]

        try:
            jobs_count, relevant_count = collect_company(
                company,
                board_token,
            )

            total_jobs += jobs_count
            total_relevant += relevant_count
            successful_sources += 1

        except requests.RequestException as error:
            failed_sources += 1

            print(f"ERROR collecting {company}")
            print(f"Reason: {error}")
            print()

        except Exception as error:
            failed_sources += 1

            print(f"UNEXPECTED ERROR collecting {company}")
            print(f"Reason: {error}")
            print()

    print("=" * 80)
    print("JOB COLLECTION COMPLETE")
    print("=" * 80)
    print()
    print(f"Companies configured: {len(greenhouse_sources)}")
    print(f"Companies collected successfully: {successful_sources}")
    print(f"Companies failed: {failed_sources}")
    print(f"Total jobs collected: {total_jobs}")
    print(f"Total relevant jobs: {total_relevant}")
    print("Jobs saved to data/jobs.db")
    print()


if __name__ == "__main__":
    main()