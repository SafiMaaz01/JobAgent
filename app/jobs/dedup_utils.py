import hashlib
import json
import re
import string
import urllib.parse
from typing import Set, Any
from .normalize import html_to_text

# Simple stopwords list for token cleaning
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "in", "on", "with",
    "for", "to", "of", "by", "at", "from", "up", "out", "as", "is",
    "it", "this", "that", "these", "those", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did",
    "our"
}

def compute_dedup_key(url: str) -> str | None:
    """Return a deterministic SHA‑256 hash of a normalized URL.
    Returns ``None`` when ``url`` is empty.
    """
    if not url:
        return None
    # Use conservative URL normalisation (scheme/hostname lower‑cased, trailing slash removed)
    norm = _normalize_url(url)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()

# Helper for conservative URL normalization
def _normalize_url(url: str) -> str:
    """Normalize URL for deduplication.
    - Strip surrounding whitespace.
    - Lower‑case scheme and hostname.
    - Remove a trailing slash on the path.
    - Preserve case‑sensitive path and query components.
    """
    url = url.strip()
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip('/')
    # Re‑assemble preserving query and fragment (fragment not used for dedup)
    return urllib.parse.urlunparse((scheme, netloc, path, "", parsed.query, ""))

def canonicalize_text(text: str) -> str:
    """Lower‑case and trim text for canonical comparisons."""
    return text.strip().lower()

# Aliases for location normalisation (Bangalore ↔ Bengaluru)
_LOCATION_ALIASES = {
    "bangalore": "bangalore",
    "bengaluru": "bangalore",
}

def canonicalize_location(loc: str) -> str:
    """Normalise location strings for deduplication while preserving display.
    Currently treats Bangalore and Bengaluru as equivalent.
    """
    if not loc:
        return ""
    key = loc.strip().lower()
    return _LOCATION_ALIASES.get(key, key)
    """Lower‑case and trim text for canonical comparisons."""
    return text.strip().lower()

def description_tokens(description: str) -> Set[str]:
    """Convert a job description into a token set.
    Steps:
    1. Strip HTML to plain text.
    2. Lower‑case.
    3. Remove punctuation.
    4. Split on whitespace.
    5. Remove stop‑words.
    """
    plain = html_to_text(description)
    plain = plain.lower()
    # Replace punctuation with spaces using ASCII punctuation set
    plain = re.sub(f"[{re.escape(string.punctuation)}]", " ", plain)
    tokens = {tok for tok in re.split(r"\s+", plain) if tok}
    return {tok for tok in tokens if tok not in STOPWORDS}

def jaccard_similarity(a: Set[str], b: Set[str]) -> float:
    """Compute Jaccard similarity between two token sets."""
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0

def merge_provenance(existing: str, new_entry: Any) -> str:
    """Merge a new provenance dict into existing JSON array string without duplicating entries.
    ``existing`` may be ``None`` or malformed JSON.
    Returns a JSON string.
    """
    try:
        prov = json.loads(existing) if existing else []
        if not isinstance(prov, list):
            prov = []
    except (json.JSONDecodeError, TypeError):
        prov = []

    # Check if entry with same source + external_id already exists in provenance
    for item in prov:
        if (
            isinstance(item, dict)
            and item.get("source") == new_entry.get("source")
            and str(item.get("external_id", "")) == str(new_entry.get("external_id", ""))
        ):
            # Update url if new_entry has one
            if new_entry.get("url"):
                item["url"] = new_entry.get("url")
            return json.dumps(prov, ensure_ascii=False)

    prov.append(new_entry)
    return json.dumps(prov, ensure_ascii=False)


# ----------------------------------------------------------------------
# Provenance entry helper – ensures required fields are always present
# ----------------------------------------------------------------------
def make_provenance_entry(source: str, external_id: str, url: str) -> dict:
    """Return a provenance dict with the mandatory keys.
    The deduplication layer must use this helper to guarantee that every
    entry contains ``source``, ``external_id`` and ``url``.
    """
    return {
        "source": source,
        "external_id": str(external_id),
        "url": url or "",
    }


# ----------------------------------------------------------------------
# Stats container used by the deduplication layer to report deduplication metrics.
# ----------------------------------------------------------------------
class DedupStats:
    def __init__(self) -> None:
        self.inserted: int = 0
        self.existing_source_records: int = 0
        self.candidate_groups: int = 0
        self.merged_groups: int = 0
        self.unmerged_candidates: int = 0
        self.conflicts: int = 0

