# tests/test_job_sources.py
"""Unit tests for Phase 1A job source adapters and collector.
These tests use monkeypatching to replace network calls with mock data
and to isolate failure handling. No real HTTP requests are made.
"""

import json
import types
from typing import List, Dict, Any

import pytest

# Import modules under test
from app.jobs import lever, remoteok, collector
from app.jobs.filter import is_relevant_job

# Helper mock response object
class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

# ---------- LeverSource tests ----------

def test_lever_adapter_parsing(monkeypatch):
    """Verify LeverSource correctly normalises a typical payload."""
    sample_payload = [
        {
            "id": "12345",
            "text": "Software Engineer",
            "categories": {"location": "Remote"},
            "hostedUrl": "https://jobs.lever.co/example/12345",
            "description": "Develop awesome software.",
            "postedAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-02T00:00:00Z",
        }
    ]
    # Patch requests.get used inside LeverSource._request
    monkeypatch.setattr(lever, "requests", types.SimpleNamespace(get=lambda url, timeout=None: MockResponse(sample_payload)))
    # Force deterministic filter to always return True
    monkeypatch.setattr(lever, "is_relevant_job", lambda _: True)

    source = lever.LeverSource({"company": "ExampleCo", "slug": "example"})
    jobs = source.fetch_jobs()
    assert isinstance(jobs, list) and len(jobs) == 1
    job = jobs[0]
    # Verify required canonical fields are present and correctly mapped
    assert job["source"] == "lever"
    assert job["external_id"] == "12345"
    assert job["company"] == "ExampleCo"
    assert job["title"] == "Software Engineer"
    assert job["location"] == "Remote"
    assert job["url"] == "https://jobs.lever.co/example/12345"
    assert job["description"] == "Develop awesome software."
    assert job["posted_at"] == "2024-01-01T00:00:00Z"
    assert job["updated_at"] == "2024-01-02T00:00:00Z"
    assert job["is_relevant"] is True

def test_lever_adapter_malformed_data(monkeypatch):
    """Adapter should handle missing optional fields without raising."""
    malformed_payload = [
        {
            "id": "999",
            "text": "Data Scientist",
            # 'categories' missing
            "hostedUrl": "https://jobs.lever.co/xyz/999",
            # 'description' missing
            "postedAt": None,
            "updatedAt": None,
        }
    ]
    monkeypatch.setattr(lever, "requests", types.SimpleNamespace(get=lambda url, timeout=None: MockResponse(malformed_payload)))
    monkeypatch.setattr(lever, "is_relevant_job", lambda _: False)
    source = lever.LeverSource({"company": "XYZCorp", "slug": "xyz"})
    jobs = source.fetch_jobs()
    job = jobs[0]
    assert job["location"] == ""
    assert job["description"] == ""
    assert job["is_relevant"] is False

# ---------- RemoteOKSource tests ----------

def test_remoteok_adapter_parsing(monkeypatch):
    sample_payload = [
        {
            "id": 777,
            "company": "RemoteCo",
            "position": "Full‑Stack Engineer",
            "location": "Worldwide",
            "url": "https://remoteok.com/remote-jobs/777",
            "description": "Work on cloud platforms.",
            "date": "2024-02-15",
        }
    ]
    monkeypatch.setattr(remoteok, "requests", types.SimpleNamespace(get=lambda url, timeout=None: MockResponse(sample_payload)))
    monkeypatch.setattr(remoteok, "is_relevant_job", lambda _: True)
    source = remoteok.RemoteOKSource()
    jobs = source.fetch_jobs()
    assert len(jobs) == 1
    job = jobs[0]
    assert job["source"] == "remoteok"
    assert job["external_id"] == "777"
    assert job["company"] == "RemoteCo"
    assert job["title"] == "Full‑Stack Engineer"
    assert job["location"] == "Worldwide"
    assert job["url"] == "https://remoteok.com/remote-jobs/777"
    assert job["description"] == "Work on cloud platforms."
    assert job["posted_at"] == "2024-02-15"
    assert job["is_relevant"] is True

def test_remoteok_adapter_malformed(monkeypatch):
    malformed_payload = [
        {
            "id": 888,
            # Missing many fields
        }
    ]
    monkeypatch.setattr(remoteok, "requests", types.SimpleNamespace(get=lambda url, timeout=None: MockResponse(malformed_payload)))
    monkeypatch.setattr(remoteok, "is_relevant_job", lambda _: False)
    source = remoteok.RemoteOKSource()
    jobs = source.fetch_jobs()
    job = jobs[0]
    assert job["company"] == ""
    assert job["title"] == ""
    assert job["location"] == ""
    assert job["url"] == ""
    assert job["description"] == ""
    assert job["is_relevant"] is False

# ---------- Collector fault‑tolerance tests ----------

def test_collector_continues_on_source_failure(monkeypatch, capsys):
    """When one source raises an exception, the collector should still process others."""
    # Mock configuration to include both sources
    fake_config = {"lever": [{"company": "A", "slug": "a"}], "remoteok": {"enabled": True}}
    monkeypatch.setattr(collector, "load_config", lambda: fake_config)

    # Patch upsert_job_with_dedup to be a no-op returning 'inserted'
    monkeypatch.setattr(collector, "upsert_job_with_dedup", lambda conn, job, logs, stats: "inserted")

    # Create a LeverSource that raises
    class FailingLever(lever.LeverSource):
        def fetch_jobs(self):
            raise RuntimeError("Simulated failure")
    monkeypatch.setattr(collector, "LeverSource", FailingLever)

    # Mock RemoteOK to return a single normalised job
    sample_remote = [
        {
            "id": 1,
            "company": "RemoteCo",
            "position": "Dev",
            "location": "Anywhere",
            "url": "https://example.com",
            "description": "Dev job",
            "date": "2024-01-01",
        }
    ]
    monkeypatch.setattr(remoteok, "requests", types.SimpleNamespace(get=lambda *args, **kwargs: MockResponse(sample_remote)))
    monkeypatch.setattr(remoteok, "is_relevant_job", lambda _: True)

    collector.collect_all()
    captured = capsys.readouterr().out
    assert "[LEVER] FAILED" in captured
    assert "[REMOTEOK] Collected" in captured
    assert "Sources succeeded: 1" in captured
    assert "Sources failed: 1" in captured

def test_collector_handles_partial_remoteok_failure(monkeypatch, capsys):
    """RemoteOK returning a HTTP error should not abort the whole run."""
    fake_config = {"lever": [], "remoteok": {"enabled": True}}
    monkeypatch.setattr(collector, "load_config", lambda: fake_config)
    monkeypatch.setattr(collector, "upsert_job_with_dedup", lambda conn, job, logs, stats: "inserted")

    class BadResponse:
        status_code = 500
        def raise_for_status(self):
            raise Exception("500 Server Error")
        def json(self):
            return []
    monkeypatch.setattr(remoteok, "requests", types.SimpleNamespace(get=lambda *args, **kwargs: BadResponse()))

    collector.collect_all()
    captured = capsys.readouterr().out
    assert "[REMOTEOK] FAILED" in captured
    assert "Sources succeeded: 0" in captured
    assert "Sources failed: 1" in captured
