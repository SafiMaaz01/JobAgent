"""Deterministic cross-source deduplication engine for JobAgent V2.

Implements a 3-level deterministic deduplication policy:
- Existing Same-Source Check: Idempotent refresh of same source + external_id record.
  Does NOT increment merged_groups; increments existing_source_records.
- Level 1 (Certain Duplicate): Exact normalized URL match from another source.
  Merges provenance and increments merged_groups.
- Level 2 (Strong Duplicate): Exact match on canonical company, title, and location,
  AND description Jaccard token similarity >= 0.75 across different records.
  Merges provenance and increments merged_groups.
- Level 3 (Uncertain): No duplicate match. Inserted as a new job listing.
  Increments inserted.

Guarantees:
- Authoritative workflow state preservation (review_status, applied_at, match_score, etc.).
- Provenance tracking across all contributing sources without data loss.
- Non-destructive conflict isolation if conflicting non-default workflow states occur.
- 100% deterministic (no ML, no LLM, no probabilistic heuristics).
"""

import json
from typing import Any, Dict, List, Optional

from .dedup_utils import (
    DedupStats,
    canonicalize_location,
    canonicalize_text,
    compute_dedup_key,
    description_tokens,
    jaccard_similarity,
    make_provenance_entry,
    merge_provenance,
    _normalize_url,
)

# Authoritative workflow fields that must be preserved
WORKFLOW_FIELDS = [
    "review_status",
    "reviewed_at",
    "applied_at",
    "match_score",
    "recommendation",
    "match_details",
]

# Unset/default values for workflow fields that do NOT represent an active user/pipeline decision
DEFAULT_WORKFLOW_VALUES = {
    "review_status": {None, "", "pending"},
    "reviewed_at": {None, ""},
    "applied_at": {None, ""},
    "match_score": {None},
    "recommendation": {None, ""},
    "match_details": {None, ""},
}


def _get_workflow_conflict(
    existing: Dict[str, Any], incoming: Dict[str, Any]
) -> Optional[str]:
    """Check if incoming record has conflicting non-default workflow state with existing row.

    Returns description of the conflict, or None if safe to merge.
    """
    for field in WORKFLOW_FIELDS:
        ev = existing[field] if field in existing.keys() else None
        iv = incoming.get(field)

        ev_is_set = ev not in DEFAULT_WORKFLOW_VALUES.get(field, {None, ""})
        iv_is_set = iv not in DEFAULT_WORKFLOW_VALUES.get(field, {None, ""})

        # Conflict occurs if BOTH records have explicit non-default values that disagree
        if ev_is_set and iv_is_set and ev != iv:
            return f"{field} conflict (existing='{ev}', incoming='{iv}')"

    return None


def _canonical_key(job: Dict[str, Any]) -> tuple[str, str, str]:
    """Return tuple of canonicalized (company, title, location) for Level 2 grouping."""
    company = canonicalize_text(job.get("company") or "")
    title = canonicalize_text(job.get("title") or "")
    location = canonicalize_location(job.get("location") or "")
    return (company, title, location)


def _insert_row(conn, job: Dict[str, Any], prov_entry: Dict[str, Any], dedup_key: Optional[str]) -> None:
    """Insert a job row into the database with full provenance and dedup_key."""
    cur = conn.execute("PRAGMA table_info(jobs)")
    table_cols = {row["name"] for row in cur.fetchall()}

    provenance_json = json.dumps([prov_entry], ensure_ascii=False)

    insert_dict = {}
    for k, v in job.items():
        if k.startswith("_"):
            continue
        if k in table_cols:
            insert_dict[k] = v

    if "source_provenance" in table_cols and "source_provenance" not in insert_dict:
        insert_dict["source_provenance"] = provenance_json
    elif "source_provenance" in insert_dict and not insert_dict["source_provenance"]:
        insert_dict["source_provenance"] = provenance_json

    if "dedup_key" in table_cols and "dedup_key" not in insert_dict:
        insert_dict["dedup_key"] = dedup_key

    cols = list(insert_dict.keys())
    placeholders = ["?"] * len(cols)
    values = [insert_dict[c] for c in cols]

    sql = f"INSERT INTO jobs ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
    conn.execute(sql, tuple(values))
    conn.commit()


def _update_same_source_row(
    conn, existing_row: Any, job: Dict[str, Any], prov_entry: Dict[str, Any], dedup_key: Optional[str]
) -> None:
    """Update an existing same-source record's content fields without touching workflow fields."""
    existing_prov = existing_row["source_provenance"] if "source_provenance" in existing_row.keys() else None
    new_prov = merge_provenance(existing_prov, prov_entry)

    conn.execute(
        """
        UPDATE jobs
        SET title = ?,
            location = ?,
            url = ?,
            description = ?,
            updated_at = ?,
            is_relevant = ?,
            dedup_key = COALESCE(dedup_key, ?),
            source_provenance = ?
        WHERE id = ?
        """,
        (
            job.get("title", existing_row["title"]),
            job.get("location", existing_row["location"]),
            job.get("url", existing_row["url"]),
            job.get("description", existing_row["description"]),
            job.get("updated_at", existing_row["updated_at"]),
            int(job.get("is_relevant", existing_row["is_relevant"] or 0)),
            dedup_key,
            new_prov,
            existing_row["id"],
        ),
    )
    conn.commit()


def _merge_into_row(conn, existing_row: Any, prov_entry: Dict[str, Any], stats: DedupStats) -> None:
    """Safely merge cross-source provenance into existing database row without altering workflow state."""
    existing_prov = existing_row["source_provenance"] if "source_provenance" in existing_row.keys() else None
    new_prov = merge_provenance(existing_prov, prov_entry)

    conn.execute(
        "UPDATE jobs SET source_provenance = ? WHERE id = ?",
        (new_prov, existing_row["id"]),
    )
    conn.commit()
    stats.merged_groups += 1


def upsert_job_with_dedup(
    conn,
    job: Dict[str, Any],
    conflict_logs: List[str],
    stats: DedupStats,
) -> str:
    """Insert or merge a job row according to the 3-level deduplication policy.

    Parameters:
        conn: SQLite database connection (with sqlite3.Row factory).
        job: Dictionary of job fields.
        conflict_logs: Mutable list to append conflict details into.
        stats: DedupStats instance to track candidate groups, merges, and conflicts.

    Returns:
        One of: "inserted", "merged", "existing", "conflict".
    """
    raw_url = job.get("url") or ""
    norm_url = _normalize_url(raw_url)
    dedup_key = job.get("_dedup_key") or compute_dedup_key(raw_url)
    job["_dedup_key"] = dedup_key

    prov_entry = make_provenance_entry(
        job.get("source", "unknown"),
        str(job.get("external_id", "")),
        raw_url,
    )

    # =========================================================================
    # Step 1: Same Source Record Check (source + external_id match)
    # =========================================================================
    same_source_row = None
    if job.get("source") and job.get("external_id") is not None:
        same_source_row = conn.execute(
            "SELECT * FROM jobs WHERE source = ? AND external_id = ?",
            (job.get("source"), str(job.get("external_id"))),
        ).fetchone()

    if same_source_row:
        conflict = _get_workflow_conflict(same_source_row, job)
        if conflict:
            conflict_msg = (
                f"Conflict on same-source record (existing id={same_source_row['id']}, "
                f"source={job.get('source')}, ext_id={job.get('external_id')}): {conflict}"
            )
            conflict_logs.append(conflict_msg)
            stats.conflicts += 1
            _insert_row(conn, job, prov_entry, dedup_key)
            return "conflict"

        _update_same_source_row(conn, same_source_row, job, prov_entry, dedup_key)
        stats.existing_source_records += 1
        return "existing"

    # =========================================================================
    # Step 2: Level 1 Certain Duplicate (Normalized URL match from another source)
    # =========================================================================
    url_match_row = None
    if raw_url:
        if dedup_key:
            url_match_row = conn.execute(
                "SELECT * FROM jobs WHERE dedup_key = ?", (dedup_key,)
            ).fetchone()
        if not url_match_row:
            url_match_row = conn.execute(
                "SELECT * FROM jobs WHERE url = ?", (raw_url,)
            ).fetchone()

    if url_match_row:
        conflict = _get_workflow_conflict(url_match_row, job)
        if conflict:
            conflict_msg = (
                f"Conflict on Level 1 URL match (existing id={url_match_row['id']}, "
                f"source={job.get('source')}, ext_id={job.get('external_id')}): {conflict}"
            )
            conflict_logs.append(conflict_msg)
            stats.conflicts += 1
            _insert_row(conn, job, prov_entry, dedup_key)
            return "conflict"

        _merge_into_row(conn, url_match_row, prov_entry, stats)
        return "merged"

    # =========================================================================
    # Step 3: Level 2 Strong Duplicate (Canonical company + title + location & Jaccard >= 0.75)
    # =========================================================================
    target_key = _canonical_key(job)

    # Fetch all existing jobs to evaluate canonical candidate equivalence
    all_rows = conn.execute("SELECT * FROM jobs").fetchall()
    canonical_candidates = [
        row for row in all_rows if _canonical_key(dict(row)) == target_key
    ]

    if canonical_candidates:
        stats.candidate_groups += 1
        incoming_tokens = description_tokens(job.get("description") or "")

        for candidate in canonical_candidates:
            cand_tokens = description_tokens(candidate["description"] or "")
            sim = jaccard_similarity(incoming_tokens, cand_tokens)

            if sim >= 0.75:
                conflict = _get_workflow_conflict(candidate, job)
                if conflict:
                    conflict_msg = (
                        f"Conflict on Level 2 canonical match (existing id={candidate['id']}, "
                        f"company='{job.get('company')}', title='{job.get('title')}'): {conflict}"
                    )
                    conflict_logs.append(conflict_msg)
                    stats.conflicts += 1
                    _insert_row(conn, job, prov_entry, dedup_key)
                    return "conflict"

                _merge_into_row(conn, candidate, prov_entry, stats)
                return "merged"

        # Candidates matched on metadata but failed description similarity threshold
        stats.unmerged_candidates += 1

    # =========================================================================
    # Step 4: Level 3 Uncertain (No duplicate found -> Insert as new listing)
    # =========================================================================
    _insert_row(conn, job, prov_entry, dedup_key)
    stats.inserted += 1
    return "inserted"
