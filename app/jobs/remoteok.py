import json
import time
from typing import List, Dict, Any

import requests

from app.jobs.source_interface import JobSource
from app.jobs.filter import is_relevant_job


class RemoteOKSource:
    """Adapter for RemoteOK public JSON feed.

    The feed returns a list of job objects. We preserve the original ``url``
    field as ``url`` in the canonical job dict.
    """

    source_name = "remoteok"
    FEED_URL = "https://remoteok.com/api"

    def __init__(self, config: Dict[str, Any] | None = None):
        # Config currently unused but kept for future extensibility.
        self.enabled = True
        if config is not None:
            self.enabled = bool(config.get("enabled", True))

    def _request(self) -> List[Dict[str, Any]]:
        backoff = 1
        while True:
            response = requests.get(self.FEED_URL, timeout=30)
            if response.status_code == 200:
                return response.json()
            if response.status_code == 429:
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                continue
            response.raise_for_status()

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        raw_jobs = self._request()
        normalized: List[Dict[str, Any]] = []
        for raw in raw_jobs:
            # RemoteOK fields (based on their public API)
            external_id = str(raw.get("id"))
            company = raw.get("company", "").strip()
            title = raw.get("position", "").strip()
            location = raw.get("location", "").strip()
            url = raw.get("url", "").strip()
            description = raw.get("description", "").strip()
            posted_at = raw.get("date", None)  # ISO string may be present
            updated_at = None

            # Build a minimal dict for deterministic filter.
            filter_raw = {
                "title": title,
                "location": {"name": location},
                "content": description,
            }
            is_relevant = is_relevant_job(filter_raw)

            normalized.append({
                "source": self.source_name,
                "external_id": external_id,
                "company": company,
                "title": title,
                "location": location,
                "url": url,  # Preserve original posting URL
                "description": description,
                "posted_at": posted_at,
                "updated_at": updated_at,
                "is_relevant": is_relevant,
            })
        return normalized
