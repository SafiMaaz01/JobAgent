"""Comprehensive unit tests for deterministic cross-source deduplication layer.

Tests all required deduplication behaviors and semantic statistics using an in-memory SQLite database:
1. Same normalized URL across sources -> merged (Level 1)
2. Same source + external_id -> existing_source_records (idempotent, NOT merged_groups)
3. Bangalore/Bengaluru alias -> canonicalized & merged (Level 2)
4. Company/title/location equal & Jaccard >= 0.75 -> merged (Level 2)
5. Company/title/location equal & Jaccard < 0.75 -> not merged (unmerged_candidates, Level 3)
6. Different company/title/location -> not merged (Level 3 insert)
7. HTML stripped before tokenization
8. Provenance contains every contributing source without duplicates
9. Workflow state conflict -> conflict reported -> rows remain separate
10. review_status="applied" and applied_at remain unchanged after merge
11. match_score, recommendation, match_details remain unchanged after merge
12. DedupStats counters are correct and semantically distinct
13. Multiple refreshes of same source do not inflate merged_groups
"""

import json
import sqlite3
import pytest

from app.jobs.dedup import upsert_job_with_dedup
from app.jobs.dedup_utils import DedupStats, description_tokens, make_provenance_entry


def create_test_connection():
    """Create an in-memory SQLite database with the full schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            location TEXT,
            url TEXT NOT NULL,
            description TEXT,
            posted_at TEXT,
            updated_at TEXT,
            is_relevant INTEGER DEFAULT 0,
            match_score INTEGER,
            recommendation TEXT,
            matched_at TEXT,
            match_details TEXT,
            review_status TEXT DEFAULT 'pending',
            reviewed_at TEXT,
            applied_at TEXT,
            dedup_key TEXT,
            source_provenance TEXT,
            UNIQUE(source, external_id)
        )
        """
    )
    conn.commit()
    return conn


@pytest.fixture()
def db_conn():
    conn = create_test_connection()
    yield conn
    conn.close()


def test_1_same_normalized_url_merged(db_conn):
    """1. Same normalized URL from another source -> merged via Level 1."""
    stats = DedupStats()
    conflict_logs = []
    job1 = {
        "source": "lever",
        "external_id": "101",
        "company": "Acme Corp",
        "title": "Frontend Engineer",
        "location": "Remote",
        "url": "https://example.com/jobs/frontend-dev/",
        "description": "Build modern UI components in React.",
    }
    res1 = upsert_job_with_dedup(db_conn, job1, conflict_logs, stats)
    assert res1 == "inserted"

    # Incoming job from another source with slight URL variation (trailing slash removed)
    job2 = {
        "source": "remoteok",
        "external_id": "rok-202",
        "company": "Acme",
        "title": "Frontend Dev",
        "location": "Remote",
        "url": "https://example.com/jobs/frontend-dev",
        "description": "React developer wanted.",
    }
    res2 = upsert_job_with_dedup(db_conn, job2, conflict_logs, stats)
    assert res2 == "merged"

    row = db_conn.execute("SELECT * FROM jobs").fetchone()
    prov = json.loads(row["source_provenance"])
    assert len(prov) == 2
    assert prov[0]["source"] == "lever"
    assert prov[1]["source"] == "remoteok"
    assert stats.merged_groups == 1
    assert stats.existing_source_records == 0


def test_2_same_source_and_external_id_idempotent(db_conn):
    """2. Same source + external_id -> updated as existing_source_records (NOT merged_groups)."""
    stats = DedupStats()
    conflict_logs = []
    job1 = {
        "source": "greenhouse",
        "external_id": "gh-999",
        "company": "Beta Soft",
        "title": "Fullstack Engineer",
        "location": "New York",
        "url": "https://beta.com/jobs/1",
        "description": "Fullstack development in TypeScript and Node.",
    }
    res1 = upsert_job_with_dedup(db_conn, job1, conflict_logs, stats)
    assert res1 == "inserted"

    # Re-collecting the exact same source record
    job2 = {
        "source": "greenhouse",
        "external_id": "gh-999",
        "company": "Beta Soft",
        "title": "Fullstack Engineer (Updated)",
        "location": "New York",
        "url": "https://beta.com/jobs/1",
        "description": "Fullstack development in TypeScript and Node with GraphQL.",
    }
    res2 = upsert_job_with_dedup(db_conn, job2, conflict_logs, stats)
    assert res2 == "existing"
    assert stats.existing_source_records == 1
    assert stats.merged_groups == 0  # Crucial: Must NOT inflate merged_groups

    row = db_conn.execute("SELECT * FROM jobs").fetchone()
    prov = json.loads(row["source_provenance"])
    assert len(prov) == 1  # Crucial: Must NOT duplicate provenance
    assert row["title"] == "Fullstack Engineer (Updated)"


def test_3_bangalore_bengaluru_alias_canonicalized(db_conn):
    """3. Bangalore/Bengaluru alias -> canonicalized & merged via Level 2."""
    stats = DedupStats()
    conflict_logs = []
    job1 = {
        "source": "lever",
        "external_id": "lev-1",
        "company": "TechNova",
        "title": "React Developer",
        "location": "Bangalore",
        "url": "https://technova.com/jobs/1",
        "description": "Develop scalable web applications with React and Redux.",
    }
    upsert_job_with_dedup(db_conn, job1, conflict_logs, stats)

    job2 = {
        "source": "remoteok",
        "external_id": "rok-1",
        "company": "TechNova",
        "title": "React Developer",
        "location": "Bengaluru",
        "url": "https://technova.com/careers/2",
        "description": "Develop scalable web applications with React and Redux.",
    }
    res = upsert_job_with_dedup(db_conn, job2, conflict_logs, stats)
    assert res == "merged"
    prov = json.loads(db_conn.execute("SELECT source_provenance FROM jobs").fetchone()[0])
    assert len(prov) == 2
    assert stats.merged_groups == 1


def test_4_company_title_location_equal_jaccard_above_threshold(db_conn):
    """4. Company/title/location equal & Jaccard >= 0.75 -> merged via Level 2."""
    stats = DedupStats()
    conflict_logs = []
    job1 = {
        "source": "lever",
        "external_id": "l-100",
        "company": "CloudCorp",
        "title": "Software Engineer",
        "location": "Hyderabad",
        "url": "https://cloudcorp.com/apply/1",
        "description": "Join our team building cloud platforms. Experience with Python, Docker, and Kubernetes required.",
    }
    upsert_job_with_dedup(db_conn, job1, conflict_logs, stats)

    # Slight rewording but very high token overlap (Jaccard >= 0.75)
    job2 = {
        "source": "remoteok",
        "external_id": "r-100",
        "company": "CloudCorp",
        "title": "Software Engineer",
        "location": "Hyderabad",
        "url": "https://cloudcorp.com/apply/2",
        "description": "Join our team building cloud platforms. Experience with Python, Docker, Kubernetes required.",
    }
    res = upsert_job_with_dedup(db_conn, job2, conflict_logs, stats)
    assert res == "merged"
    assert stats.candidate_groups == 1
    assert stats.merged_groups == 1
    assert stats.unmerged_candidates == 0


def test_5_company_title_location_equal_jaccard_below_threshold(db_conn):
    """5. Company/title/location equal & Jaccard < 0.75 -> not merged (unmerged candidate)."""
    stats = DedupStats()
    conflict_logs = []
    job1 = {
        "source": "lever",
        "external_id": "l-201",
        "company": "Epsilon",
        "title": "Backend Engineer",
        "location": "Pune",
        "url": "https://epsilon.com/jobs/backend-go",
        "description": "Work on high-throughput backend microservices using Golang and gRPC.",
    }
    upsert_job_with_dedup(db_conn, job1, conflict_logs, stats)

    # Completely different description (different role under same title)
    job2 = {
        "source": "remoteok",
        "external_id": "r-202",
        "company": "Epsilon",
        "title": "Backend Engineer",
        "location": "Pune",
        "url": "https://epsilon.com/jobs/backend-java",
        "description": "Maintain legacy enterprise ERP systems built in Java Spring Hibernate.",
    }
    res = upsert_job_with_dedup(db_conn, job2, conflict_logs, stats)
    assert res == "inserted"
    assert stats.candidate_groups == 1
    assert stats.unmerged_candidates == 1
    assert stats.merged_groups == 0

    total_rows = db_conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    assert total_rows == 2


def test_6_different_company_title_location_not_merged(db_conn):
    """6. Different company/title/location -> not merged (inserted via Level 3)."""
    stats = DedupStats()
    conflict_logs = []
    job1 = {
        "source": "lever",
        "external_id": "z-1",
        "company": "Alpha Tech",
        "title": "Fullstack Developer",
        "location": "Remote",
        "url": "https://alpha.com/job/1",
        "description": "Fullstack role at Alpha.",
    }
    upsert_job_with_dedup(db_conn, job1, conflict_logs, stats)

    job2 = {
        "source": "remoteok",
        "external_id": "z-2",
        "company": "Beta Labs",
        "title": "Frontend Developer",
        "location": "Mumbai",
        "url": "https://beta.com/job/2",
        "description": "Frontend role at Beta.",
    }
    res = upsert_job_with_dedup(db_conn, job2, conflict_logs, stats)
    assert res == "inserted"
    assert stats.candidate_groups == 0
    assert stats.merged_groups == 0

    total_rows = db_conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    assert total_rows == 2


def test_7_html_stripped_before_tokenization():
    """7. HTML stripped before tokenization."""
    html_desc = "<div><h3>Senior React Engineer</h3><p>We are looking for a <b>React</b> &amp; <i>TypeScript</i> developer!</p></div>"
    tokens = description_tokens(html_desc)
    assert "senior" in tokens
    assert "react" in tokens
    assert "engineer" in tokens
    assert "typescript" in tokens
    assert "developer" in tokens
    # HTML tags must not appear as tokens
    assert "div" not in tokens
    assert "p" not in tokens
    assert "b" not in tokens
    assert "i" not in tokens
    assert "h3" not in tokens


def test_8_provenance_contains_every_contributing_source_no_duplication(db_conn):
    """8. Provenance contains every contributing source without duplicate entries."""
    stats = DedupStats()
    conflict_logs = []
    job1 = {
        "source": "greenhouse",
        "external_id": "gh-1",
        "company": "OmniCorp",
        "title": "Software Engineer",
        "location": "Remote",
        "url": "https://omni.com/gh/1",
        "description": "Engineering role at OmniCorp.",
    }
    upsert_job_with_dedup(db_conn, job1, conflict_logs, stats)

    job2 = {
        "source": "lever",
        "external_id": "lev-2",
        "company": "OmniCorp",
        "title": "Software Engineer",
        "location": "Remote",
        "url": "https://omni.com/lever/2",
        "description": "Engineering role at OmniCorp.",
    }
    upsert_job_with_dedup(db_conn, job2, conflict_logs, stats)

    # Re-collect job1 from greenhouse (should NOT duplicate entry)
    upsert_job_with_dedup(db_conn, job1, conflict_logs, stats)

    row = db_conn.execute("SELECT source_provenance FROM jobs").fetchone()
    prov = json.loads(row["source_provenance"])
    assert len(prov) == 2
    sources = [p["source"] for p in prov]
    assert sources == ["greenhouse", "lever"]


def test_9_workflow_state_conflict_reported(db_conn):
    """9. Workflow state conflict -> conflict reported -> rows remain separate."""
    stats = DedupStats()
    conflict_logs = []
    job_existing = {
        "source": "lever",
        "external_id": "c-1",
        "company": "TargetCo",
        "title": "UI Designer",
        "location": "Delhi",
        "url": "https://target.com/jobs/1",
        "description": "Design user interfaces.",
        "review_status": "applied",
        "applied_at": "2026-01-15",
    }
    upsert_job_with_dedup(db_conn, job_existing, conflict_logs, stats)

    # Incoming job has explicit conflicting review decision
    job_incoming = {
        "source": "remoteok",
        "external_id": "c-2",
        "company": "TargetCo",
        "title": "UI Designer",
        "location": "Delhi",
        "url": "https://target.com/jobs/1",  # Same URL to trigger Level 1 match
        "description": "Design user interfaces.",
        "review_status": "rejected",  # Conflicting decision!
        "applied_at": "2026-02-20",
    }
    res = upsert_job_with_dedup(db_conn, job_incoming, conflict_logs, stats)
    assert res == "conflict"
    assert stats.conflicts == 1
    assert len(conflict_logs) >= 1
    assert "review_status conflict" in conflict_logs[0]

    rows = db_conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    assert rows == 2


def test_10_review_status_applied_and_applied_at_remain_unchanged(db_conn):
    """10. review_status='applied' and applied_at remain unchanged after merge."""
    stats = DedupStats()
    conflict_logs = []
    job1 = {
        "source": "greenhouse",
        "external_id": "a-1",
        "company": "AppCo",
        "title": "Lead Developer",
        "location": "Bangalore",
        "url": "https://appco.com/job/1",
        "description": "Lead web development team.",
        "review_status": "applied",
        "applied_at": "2026-03-01T10:00:00",
    }
    upsert_job_with_dedup(db_conn, job1, conflict_logs, stats)

    # Incoming fresh listing without review data
    job2 = {
        "source": "lever",
        "external_id": "a-2",
        "company": "AppCo",
        "title": "Lead Developer",
        "location": "Bangalore",
        "url": "https://appco.com/job/1",
        "description": "Lead web development team.",
        "review_status": "pending",  # default unreviewed status
        "applied_at": None,
    }
    res = upsert_job_with_dedup(db_conn, job2, conflict_logs, stats)
    assert res == "merged"

    row = db_conn.execute("SELECT * FROM jobs").fetchone()
    assert row["review_status"] == "applied"
    assert row["applied_at"] == "2026-03-01T10:00:00"


def test_11_match_score_recommendation_details_remain_unchanged(db_conn):
    """11. match_score, recommendation, match_details remain unchanged after merge."""
    stats = DedupStats()
    conflict_logs = []
    details_json = json.dumps({"skills_match": ["React", "TypeScript"], "fit": "high"})
    job1 = {
        "source": "greenhouse",
        "external_id": "m-1",
        "company": "MatchCo",
        "title": "Frontend Engineer",
        "location": "Remote",
        "url": "https://matchco.com/job/1",
        "description": "React developer role.",
        "match_score": 92,
        "recommendation": "APPLY",
        "match_details": details_json,
    }
    upsert_job_with_dedup(db_conn, job1, conflict_logs, stats)

    job2 = {
        "source": "remoteok",
        "external_id": "m-2",
        "company": "MatchCo",
        "title": "Frontend Engineer",
        "location": "Remote",
        "url": "https://matchco.com/job/1",
        "description": "React developer role.",
        "match_score": None,
        "recommendation": None,
        "match_details": None,
    }
    res = upsert_job_with_dedup(db_conn, job2, conflict_logs, stats)
    assert res == "merged"

    row = db_conn.execute("SELECT * FROM jobs").fetchone()
    assert row["match_score"] == 92
    assert row["recommendation"] == "APPLY"
    assert row["match_details"] == details_json


def test_12_dedup_stats_counters_correct_and_distinct(db_conn):
    """12. DedupStats counters are correct, non-overlapping, and semantically distinct."""
    stats = DedupStats()
    conflict_logs = []

    # 1. Insert Job A
    upsert_job_with_dedup(
        db_conn,
        {
            "source": "gh",
            "external_id": "1",
            "company": "C1",
            "title": "T1",
            "location": "L1",
            "url": "https://c1.com/1",
            "description": "Desc A with python and react",
            "review_status": "applied",
            "applied_at": "2026-01-01",
        },
        conflict_logs,
        stats,
    )
    assert stats.inserted == 1

    # 2. Idempotent refresh of Job A (same source + external_id)
    upsert_job_with_dedup(
        db_conn,
        {
            "source": "gh",
            "external_id": "1",
            "company": "C1",
            "title": "T1",
            "location": "L1",
            "url": "https://c1.com/1",
            "description": "Desc A with python and react",
        },
        conflict_logs,
        stats,
    )
    assert stats.existing_source_records == 1
    assert stats.merged_groups == 0

    # 3. Cross-source merge of Job A (from Lever with same URL)
    upsert_job_with_dedup(
        db_conn,
        {
            "source": "lev",
            "external_id": "2",
            "company": "C1",
            "title": "T1",
            "location": "L1",
            "url": "https://c1.com/1",
            "description": "Desc A with python and react",
            "review_status": "pending",
        },
        conflict_logs,
        stats,
    )
    assert stats.merged_groups == 1

    # 4. Unmerged candidate (same metadata, but different description)
    upsert_job_with_dedup(
        db_conn,
        {
            "source": "rok",
            "external_id": "3",
            "company": "C1",
            "title": "T1",
            "location": "L1",
            "url": "https://c1.com/different-3",
            "description": "Completely unrelated text about sales marketing bookkeeping",
        },
        conflict_logs,
        stats,
    )
    assert stats.candidate_groups == 1
    assert stats.unmerged_candidates == 1
    assert stats.inserted == 2

    # 5. Workflow Conflict
    upsert_job_with_dedup(
        db_conn,
        {
            "source": "remoteok",
            "external_id": "4",
            "company": "C1",
            "title": "T1",
            "location": "L1",
            "url": "https://c1.com/1",
            "description": "Desc A",
            "review_status": "rejected",
        },
        conflict_logs,
        stats,
    )
    assert stats.conflicts == 1

    assert stats.inserted == 2
    assert stats.existing_source_records == 1
    assert stats.merged_groups == 1
    assert stats.candidate_groups == 1
    assert stats.unmerged_candidates == 1
    assert stats.conflicts == 1


def test_13_multiple_refreshes_do_not_inflate_merged_groups(db_conn):
    """13. Multiple refreshes of same source do not inflate merged_groups."""
    stats = DedupStats()
    conflict_logs = []
    job = {
        "source": "greenhouse",
        "external_id": "123",
        "company": "Stripe",
        "title": "Software Engineer",
        "location": "Remote",
        "url": "https://stripe.com/jobs/123",
        "description": "Payments engineering.",
    }
    upsert_job_with_dedup(db_conn, job, conflict_logs, stats)
    assert stats.inserted == 1
    assert stats.merged_groups == 0

    # 5 successive collection runs of the same job
    for _ in range(5):
        res = upsert_job_with_dedup(db_conn, job, conflict_logs, stats)
        assert res == "existing"

    assert stats.existing_source_records == 5
    assert stats.merged_groups == 0
    row = db_conn.execute("SELECT source_provenance FROM jobs").fetchone()
    prov = json.loads(row["source_provenance"])
    assert len(prov) == 1
