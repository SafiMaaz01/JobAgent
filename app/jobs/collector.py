from collections import Counter
import json
import time
from typing import Any, Dict, List

from app.database.db import get_connection, initialize_database
from app.jobs.dedup import upsert_job_with_dedup
from app.jobs.dedup_utils import (
    DedupStats,
    canonicalize_location,
    canonicalize_text,
    compute_dedup_key,
)
from app.jobs.greenhouse_adapter import GreenhouseSource
from app.jobs.lever import LeverSource
from app.jobs.remoteok import RemoteOKSource
from app.jobs.source_interface import JobSource


def load_config() -> Dict[str, Any]:
    """Load data/sources.json configuration."""
    with open("data/sources.json", "r", encoding="utf-8") as f:
        return json.load(f)


def build_sources(config: Dict[str, Any]) -> List[JobSource]:
    sources: List[JobSource] = []
    # Greenhouse – only add if greenhouse config is present.
    if config.get("greenhouse"):
        sources.append(GreenhouseSource())
    # Lever – optional entries.
    for lever_cfg in config.get("lever", []):
        try:
            sources.append(LeverSource(lever_cfg))
        except Exception as e:
            print(f"[Lever] configuration error: {e}")
    # RemoteOK – single config dict.
    remote_cfg = config.get("remoteok", {})
    try:
        sources.append(RemoteOKSource(remote_cfg))
    except Exception as e:
        print(f"[RemoteOK] configuration error: {e}")
    return sources


def collect_all() -> None:
    initialize_database()
    config = load_config()
    sources = build_sources(config)

    # Single DB connection for the whole collection run
    connection = get_connection()

    total_jobs = 0
    total_relevant = 0
    successful_sources = 0
    failed_sources = 0
    merged_count = 0
    conflict_logs = []
    # Statistics tracker for deduplication reporting
    stats = DedupStats()

    print("=" * 80)
    print("JOB COLLECTION STARTED (Phase 1A – Source Abstraction)")
    print("=" * 80)
    print()

    for source in sources:
        source_name = getattr(source, "source_name", "unknown")
        print(f"[{source_name.upper()}] Collecting jobs...")
        try:
            jobs = source.fetch_jobs()
            # Process job with deduplication logic
            for job in jobs:
                # Compute dedup_key
                dedup_key = compute_dedup_key(job.get('url'))
                job['_dedup_key'] = dedup_key
                # Insert or merge
                result = upsert_job_with_dedup(connection, job, conflict_logs, stats)
                if result == 'merged':
                    merged_count += 1
                    # merged_groups counter is updated inside dedup layer
                total_jobs += 1
                if job.get("is_relevant"):
                    total_relevant += 1
        
            successful_sources += 1
            print(f"[{source_name.upper()}] Collected {len(jobs)} jobs (relevant {sum(j.get('is_relevant') for j in jobs)})")
        except Exception as err:
            failed_sources += 1
            print(f"[{source_name.upper()}] FAILED")
            print(f"Reason: {err}\n")
        # Respect a tiny pause between sources to avoid hammering APIs.
        time.sleep(0.5)

    print("=" * 80)
    print("JOB COLLECTION COMPLETE")
    print("=" * 80)
    print()
    print(f"Sources configured: {len(sources)}")
    print(f"Sources succeeded: {successful_sources}")
    print(f"Sources failed: {failed_sources}")
    print(f"Total jobs fetched: {total_jobs}")
    print(f"Total relevant jobs: {total_relevant}")
    print(f"Existing source records: {stats.existing_source_records}")
    print(f"Newly inserted jobs: {stats.inserted}")
    print(f"Candidate groups evaluated: {stats.candidate_groups}")
    print(f"Merged duplicate groups: {stats.merged_groups}")
    print(f"Unmerged candidates: {stats.unmerged_candidates}")
    print(f"Workflow conflicts: {stats.conflicts}")

    total_db_rows = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    total_dedup_keys = connection.execute("SELECT COUNT(*) FROM jobs WHERE dedup_key IS NOT NULL").fetchone()[0]
    total_prov = connection.execute("SELECT COUNT(*) FROM jobs WHERE source_provenance IS NOT NULL").fetchone()[0]

    print(f"Total jobs in database: {total_db_rows}")
    print(f"Dedup keys populated (in DB): {total_dedup_keys} / {total_db_rows}")
    print(f"Provenance populated (in DB): {total_prov} / {total_db_rows}")

    if conflict_logs:
        print("\nWorkflow conflicts detected during collection:")
        for msg in conflict_logs:
            print(f" - {msg}")

    # Show a few provenance examples
    examples = connection.execute("SELECT id, company, title, source_provenance FROM jobs WHERE source_provenance IS NOT NULL LIMIT 5").fetchall()
    if examples:
        print("\nProvenance examples (id: company - title -> provenance):")
        for row in examples:
            print(f" #{row['id']}: {row['company']} - {row['title']} -> {row['source_provenance']}")
    print("\nJobs saved to data/jobs.db\n")
    connection.close()


if __name__ == "__main__":
    collect_all()
