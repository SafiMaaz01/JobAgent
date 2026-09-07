import json
import time
from typing import List, Dict, Any

import requests

from app.jobs.source_interface import JobSource
from app.jobs.filter import is_relevant_job


class LeverSource:
    """Adapter for Lever public postings API.

    No authentication required. ``slug`` is the company identifier that appears
    in the Lever job board URL (e.g., ``jobs.lever.co/<slug>``).
    """

    source_name = "lever"

    def __init__(self, config: Dict[str, Any]):
        # Expect ``slug`` and ``company`` in config.
        self.company = config.get("company", "")
        self.slug = config.get("slug", "")
        if not self.slug:
            raise ValueError("Lever source configuration requires a 'slug' field")
        self.base_url = f"https://api.lever.co/v0/postings/{self.slug}?mode=json"

    def _request(self) -> List[Dict[str, Any]]:
        # Simple request with basic back‑off on 429.
        backoff = 1
        while True:
            response = requests.get(self.base_url, timeout=30)
            if response.status_code == 200:
                return response.json()
            if response.status_code == 429:
                # Too many requests – wait and retry.
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                continue
            response.raise_for_status()

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        raw_jobs = self._request()
        normalized: List[Dict[str, Any]] = []
        for raw in raw_jobs:
            # Lever fields reference: https://dev.lever.co/docs/postings-api
            external_id = str(raw.get("id"))
            title = raw.get("text", "").strip()
            location = raw.get("categories", {}).get("location", "").strip()
            url = raw.get("hostedUrl", "").strip()
            description = raw.get("description", "").strip()
            posted_at = raw.get("postedAt")
            updated_at = raw.get("updatedAt")

            # Build a minimal raw dict for deterministic filter (expects title, location dict, content).
            filter_raw = {
                "title": title,
                "location": {"name": location},
                "content": description,
            }
            is_relevant = is_relevant_job(filter_raw)

            normalized.append({
                "source": self.source_name,
                "external_id": external_id,
                "company": self.company or raw.get("company", {}).get("name", ""),
                "title": title,
                "location": location,
                "url": url,
                "description": description,
                "posted_at": posted_at,
                "updated_at": updated_at,
                "is_relevant": is_relevant,
            })
        return normalized
