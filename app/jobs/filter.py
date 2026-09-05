import re


MAX_EXPERIENCE_YEARS = 1


def extract_experience_requirement(text):
    if not text:
        return None

    text = text.lower()

    # Focus primarily on phrases that clearly express a requirement.
    candidates = []

    requirement_patterns = [
        # 2+ years of experience
        r"\b(\d+)\s*\+\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+|industry\s+|relevant\s+|hands[- ]on\s+)?experience\b",

        # minimum 2 years / minimum of 2 years
        r"\bminimum\s+(?:of\s+)?(\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+|industry\s+|relevant\s+|hands[- ]on\s+)?experience\b",

        # at least 2 years
        r"\bat\s+least\s+(\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+|industry\s+|relevant\s+|hands[- ]on\s+)?experience\b",

        # requires 2 years
        r"\brequires?\s+(?:a\s+)?(\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+|industry\s+|relevant\s+|hands[- ]on\s+)?experience\b",

        # 2 years of professional experience
        r"\b(\d+)\s*(?:years?|yrs?)\s+of\s+(?:professional\s+|industry\s+|relevant\s+|hands[- ]on\s+)?experience\b",

        # 2 years professional experience
        r"\b(\d+)\s*(?:years?|yrs?)\s+(?:professional\s+|industry\s+|relevant\s+|hands[- ]on\s+)?experience\b",

        # 2-4 years experience
        r"\b(\d+)\s*[-–—]\s*(\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+|industry\s+|relevant\s+|hands[- ]on\s+)?experience\b",

        # 2 to 4 years experience
        r"\b(\d+)\s+to\s+(\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+|industry\s+|relevant\s+|hands[- ]on\s+)?experience\b",
    ]

    for pattern in requirement_patterns:
        for match in re.finditer(pattern, text):
            if match.lastindex >= 2:
                # Range: use the upper bound.
                candidates.append(int(match.group(2)))
            else:
                candidates.append(int(match.group(1)))

    if not candidates:
        return None

    return max(candidates)


def get_job_text(job):
    title = job.get("title", "")
    content = job.get("content", "")
    location = job.get("location", {}).get("name", "")

    return f"{title}\n{location}\n{content}"


def is_senior_title(title):
    title = title.lower().strip()

    senior_keywords = [
        "senior",
        "sr.",
        "sr ",
        "staff",
        "principal",
        "lead",
        "manager",
        "director",
        "head of",
        "architect",
        "distinguished",
        "vp",
        "vice president",
    ]

    return any(keyword in title for keyword in senior_keywords)


TARGET_ROLE_KEYWORDS = [
    "frontend",
    "front-end",
    "front end",
    "react",
    "next.js",
    "nextjs",
    "web developer",
    "web engineer",
    "ui engineer",
    "ui developer",
    "software engineer",
    "software developer",
    "full stack",
    "full-stack",
]


EXCLUDED_KEYWORDS = [
    "backend",
    "back-end",
    "back end",
    "infrastructure",
    "platform",
    "security",
    "cybersecurity",
    "vulnerability",
    "site reliability",
    "sre",
    "devops",
    "data engineer",
    "machine learning",
    "ml engineer",
    "ai engineer",
    "embedded",
    "firmware",
    "mobile",
    "ios",
    "android",
]


EXCLUDED_NON_TECHNICAL_ROLES = [
    "operations",
    "customer support",
    "customer success",
    "support associate",
    "sales",
    "marketing",
    "recruiter",
    "recruiting",
    "compliance",
    "risk",
    "fraud",
    "financial crimes",
    "quality analyst",
    "quality assurance",
    "accounting",
    "finance",
    "legal",
    "social media",
]


ALLOWED_LOCATIONS = [
    "india",
    "remote",
    "bangalore",
    "bengaluru",
    "hyderabad",
    "pune",
    "mumbai",
    "delhi",
    "noida",
    "gurgaon",
    "gurugram",
    "chennai",
    "kolkata",
    "jamshedpur",
]


BLOCKED_LOCATIONS = [
    "us - remote",
    "us-remote",
    "usa",
    "united states",
    "canada",
    "canada-remote",
    "uk",
    "united kingdom",
    "europe",
    "brazil",
    "israel",
    "singapore",
    "australia",
    "germany",
    "france",
    "ireland",
    "netherlands",
    "switzerland",
]


UNKNOWN_LOCATION_VALUES = [
    "",
    "n/a",
    "na",
    "not specified",
    "unspecified",
    "unknown",
]


def location_matches(location, description):
    """
    Determine whether a job is potentially available in an allowed location.

    Structured location is preferred when it contains a useful location.
    If the structured location is vague (N/A, Hybrid, etc.), inspect the
    description for explicit India/allowed-location evidence.
    """

    location = (location or "").lower().strip()
    description = (description or "").lower()

    # Explicitly blocked structured locations always win.
    if any(keyword in location for keyword in BLOCKED_LOCATIONS):
        return False

    # A structured location that explicitly contains an allowed location
    # is enough.
    if any(keyword in location for keyword in ALLOWED_LOCATIONS):
        return True

    # Some Greenhouse jobs use generic structured locations such as
    # "N/A" or "Hybrid". In those cases, inspect the actual description.
    vague_location = (
        location in UNKNOWN_LOCATION_VALUES
        or location == "hybrid"
        or location == "onsite"
        or location == "on-site"
        or location == "remote"
    )

    if vague_location:
        # Explicit allowed-location evidence in the job description.
        description_patterns = [
            r"\bbengaluru\b",
            r"\bbangalore\b",
            r"\bhyderabad\b",
            r"\bpune\b",
            r"\bmumbai\b",
            r"\bdelhi\b",
            r"\bnoida\b",
            r"\bgurgaon\b",
            r"\bgurugram\b",
            r"\bchennai\b",
            r"\bkolkata\b",
            r"\bjamshedpur\b",
            r"\bindia\b",
            r"\bremote\b",
        ]

        if any(re.search(pattern, description) for pattern in description_patterns):
            return True

    return False


def filter_reason(job):
    title = job.get("title", "").lower().strip()
    location = job.get("location", {}).get("name", "").lower().strip()
    description = job.get("content", "")

    full_text = f"{title}\n{location}\n{description}".lower()

    if any(keyword in title for keyword in EXCLUDED_KEYWORDS):
        return "excluded technical role"

    if any(keyword in title for keyword in EXCLUDED_NON_TECHNICAL_ROLES):
        return "excluded non-technical role"

    if is_senior_title(title):
        return "senior-level title"

    role_match = any(
        keyword in title
        for keyword in TARGET_ROLE_KEYWORDS
    )

    if not role_match:
        return "no target role keyword in title"

    if not location_matches(location, description):
        return "location not allowed"

    required_experience = extract_experience_requirement(full_text)

    if (
        required_experience is not None
        and required_experience > MAX_EXPERIENCE_YEARS
    ):
        return (
            f"experience requirement too high "
            f"({required_experience} years)"
        )

    return None


def is_relevant_job(job):
    return filter_reason(job) is None