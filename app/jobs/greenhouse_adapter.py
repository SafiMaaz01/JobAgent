import json
import time
from typing import List, Dict, Any

import requests

from app.jobs.source_interface import JobSource
from app.jobs.normalize import normalize_greenhouse_job
from app.jobs.filter import is_relevant_job
from app.database.db import get_connection, initialize_database


class GreenhouseSource:
    """Adapter for existing Greenhouse implementation.

    Keeps compatibility with ``python -m app.jobs.greenhouse`` by providing a
    ``fetch_jobs`` method that returns a list of already‑normalized job dicts.
    """

    source_name = "greenhouse"

    def __init__(self) -> None:
        # Load configuration lazily to avoid import cycles.
        from app.jobs.greenhouse import load_sources, get_greenhouse_jobs
        self._load_sources = load_sources
        self._get_greenhouse_jobs = get_greenhouse_jobs

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        config = self._load_sources()
        greenhouse_sources = config.get("greenhouse", [])
        jobs: List[Dict[str, Any]] = []
        for src in greenhouse_sources:
            company = src.get("company")
            board_token = src.get("board_token")
            try:
                raw_jobs = self._get_greenhouse_jobs(board_token)
                for raw in raw_jobs:
                    norm = normalize_greenhouse_job(raw, company)
                    # Determine relevance using existing deterministic filter.
                    norm["is_relevant"] = is_relevant_job(raw)
                    jobs.append(norm)
            except Exception as e:
                # Propagate error upwards; collector will handle isolation.
                raise RuntimeError(f"Greenhouse source {company} failed: {e}")
        return jobs
