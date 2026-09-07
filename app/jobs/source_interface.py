from typing import Protocol, List, Dict, Any


class JobSource(Protocol):
    """Abstract interface for a job source adapter.

    Implementations must provide a ``source_name`` attribute (e.g., "greenhouse",
    "lever", "remoteok") and a ``fetch_jobs`` method returning a list of jobs in
    the canonical Job dict format defined by the application:

        {
            "source": str,
            "external_id": str,
            "company": str,
            "title": str,
            "location": str,
            "url": str,
            "description": str,
            "posted_at": str | None,
            "updated_at": str | None,
            "is_relevant": bool,
        }
    """

    source_name: str

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        """Retrieve raw job entries from the source and return them already
        normalized to the canonical dictionary shape.
        """
        ...
