import json
import re

from app.database.db import get_connection
from app.job_matcher import ask_ai, load_profile
from datetime import datetime


MAX_EXPERIENCE_YEARS = 1


# =========================================================
# Database
# =========================================================

def get_relevant_jobs():
    connection = get_connection()

    jobs = connection.execute("""
        SELECT *
        FROM jobs
        WHERE is_relevant = 1
        AND match_score IS NULL
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return jobs


# =========================================================
# JSON parsing
# =========================================================

def extract_json(text):
    if not text:
        raise ValueError("AI returned an empty response.")

    text = text.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"^```\s*",
        "",
        text,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    text = text.strip()

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            f"Could not find valid JSON in AI response:\n{text}"
        )

    json_text = text[start:end + 1]

    try:
        return json.loads(json_text)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"AI returned invalid JSON:\n{text}"
        ) from error


# =========================================================
# Candidate facts
# =========================================================

def get_candidate_facts(profile):
    """
    Build deterministic facts from the candidate profile.

    The AI should not be responsible for discovering basic facts
    such as whether the candidate has a CS degree, projects,
    programming skills, internship evidence, or education duration.
    """

    experience = profile.get("experience", [])
    education = profile.get("education", [])
    projects = profile.get("projects", [])
    skills = profile.get("skills", [])

    # ---------------------------------------------------------
    # Skills
    # ---------------------------------------------------------

    skill_names = [
        str(skill).lower().strip()
        for skill in skills
    ]

    # ---------------------------------------------------------
    # Education
    # ---------------------------------------------------------

    education_text = " ".join(
        [
            f"{item.get('degree', '')} "
            f"{item.get('institution', '')}"
            for item in education
        ]
    ).lower()

    has_cs_education = bool(
        re.search(
            r"\bcomputer science\b"
            r"|\bcomputer engineering\b"
            r"|\bcomputer application\b"
            r"|\bcs\b",
            education_text,
        )
    )

    has_education = len(education) > 0

    # Calculate education duration from structured start/end dates.
    #
    # This is intentionally separate from professional experience.
    # A job asking for "1 year of university education" must not
    # be interpreted as "1 year of work experience".
    education_months = 0

    for item in education:
        start = str(item.get("start", "")).strip()
        end = str(item.get("end", "")).strip()

        if not start or not end:
            continue

        try:
            start_date = datetime.strptime(
                start,
                "%B %Y",
            )

            end_date = datetime.strptime(
                end,
                "%B %Y",
            )

            if end_date >= start_date:
                months = (
                    (end_date.year - start_date.year) * 12
                    + (end_date.month - start_date.month)
                )

                education_months += months

        except ValueError:
            continue

    education_years = education_months / 12

    # ---------------------------------------------------------
    # Experience
    # ---------------------------------------------------------

    experience_text = " ".join(
        [
            f"{item.get('role', '')} "
            f"{item.get('company', '')} "
            f"{item.get('description', '')}"
            for item in experience
        ]
    ).lower()

    internship_experience = [
        item
        for item in experience
        if re.search(
            r"\bintern\b|\binternship\b",
            item.get("role", "").lower(),
        )
    ]

    has_internship_experience = (
        len(internship_experience) > 0
    )

    # ---------------------------------------------------------
    # Projects
    # ---------------------------------------------------------

    project_text = " ".join(
        [
            f"{item.get('name', '')} "
            f"{' '.join(item.get('technologies', []))}"
            for item in projects
        ]
    ).lower()

    has_projects = len(projects) > 0

    # ---------------------------------------------------------
    # Programming
    # ---------------------------------------------------------

    programming_skills = [
        "javascript",
        "typescript",
        "python",
        "java",
        "c++",
        "c#",
        "react",
        "react.js",
        "next.js",
        "node.js",
        "html",
        "css",
        "sql",
    ]

    has_programming_skills = any(
        skill in skill_names
        for skill in programming_skills
    )

    has_programming_projects = bool(
        project_text.strip()
    )

    # ---------------------------------------------------------
    # Locations
    # ---------------------------------------------------------

    preferred_locations = [
        str(location).lower().strip()
        for location in profile.get(
            "preferred_locations",
            [],
        )
    ]

    # ---------------------------------------------------------
    # Structured experience summary
    # ---------------------------------------------------------

    total_experience_years = profile.get(
        "years_of_experience",
        0,
    )

    return {
        "has_internship_experience": (
            has_internship_experience
        ),

        "internship_count": len(
            internship_experience
        ),

        "has_education": has_education,

        "has_cs_education": has_cs_education,

        "education_months": education_months,

        "education_years": education_years,

        "has_projects": has_projects,

        "has_programming_skills": (
            has_programming_skills
        ),

        "has_programming_projects": (
            has_programming_projects
        ),

        "skills": skill_names,

        "preferred_locations": (
            preferred_locations
        ),

        "current_location": profile.get(
            "location",
            "",
        ),

        "years_of_experience": total_experience_years,

        "experience_text": experience_text,
    }

# =========================================================
# Experience requirement detection
# =========================================================
def extract_experience_requirement(text):
    """
    Detect ONLY the minimum professional/work experience
    requirement from a job description.

    Examples:

        "1 year of professional experience" -> 1
        "2 years of experience" -> 2
        "3+ years of experience" -> 3
        "1-2 years of experience" -> 1
        "3 to 5 years of experience" -> 3

    Education-related years are ignored.

    The returned value represents the minimum professional
    experience required by the job.
    """

    if not text:
        return None

    text = text.lower()

    # ---------------------------------------------------------
    # Remove education-related phrases
    # ---------------------------------------------------------

    education_patterns = [
        r"\b\d+\s*(?:-|–|—|to)\s*\d+\s+years?\s+of\s+university\s+education\b",
        r"\b\d+\+?\s+years?\s+of\s+university\s+education\b",

        r"\b\d+\s*(?:-|–|—|to)\s*\d+\s+years?\s+of\s+university\b",
        r"\b\d+\+?\s+years?\s+of\s+university\b",

        r"\b\d+\s*(?:-|–|—|to)\s*\d+\s+years?\s+of\s+college\s+education\b",
        r"\b\d+\+?\s+years?\s+of\s+college\s+education\b",

        r"\b\d+\s*(?:-|–|—|to)\s*\d+\s+years?\s+of\s+college\b",
        r"\b\d+\+?\s+years?\s+of\s+college\b",

        r"\b\d+\s*(?:-|–|—|to)\s*\d+\s+years?\s+of\s+undergraduate\s+education\b",
        r"\b\d+\+?\s+years?\s+of\s+undergraduate\s+education\b",

        r"\b\d+\s*(?:-|–|—|to)\s*\d+\s+years?\s+of\s+undergraduate\s+study\b",
        r"\b\d+\+?\s+years?\s+of\s+undergraduate\s+study\b",

        r"\b\d+\s*(?:-|–|—|to)\s*\d+\s+years?\s+of\s+study\b",
        r"\b\d+\+?\s+years?\s+of\s+study\b",

        r"\b\d+\s*(?:-|–|—|to)\s*\d+\s+years?\s+of\s+academic\s+experience\b",
        r"\b\d+\+?\s+years?\s+of\s+academic\s+experience\b",

        r"\b\d+\s*(?:-|–|—|to)\s*\d+\s+years?\s+of\s+education\b",
        r"\b\d+\+?\s+years?\s+of\s+education\b",
    ]

    for pattern in education_patterns:
        text = re.sub(pattern, " ", text)

    requirements = []

    # ---------------------------------------------------------
    # Ranges
    #
    # "1-2 years" -> minimum is 1
    # "3-5 years" -> minimum is 3
    # ---------------------------------------------------------

    range_pattern = (
        r"\b(\d+)\s*(?:-|–|—|to)\s*(\d+)\s*"
        r"(?:years?|yrs?)"
        r"(?:\s+(?:of\s+)?(?:professional\s+|work\s+)?experience)\b"
    )

    range_matches = list(re.finditer(range_pattern, text))

    for match in range_matches:
        first_year = int(match.group(1))
        second_year = int(match.group(2))

        requirements.append(
            min(first_year, second_year)
        )

    # Replace ranges with spaces so the individual numbers
    # cannot be detected again by the other patterns.
    text_without_ranges = re.sub(
        range_pattern,
        " ",
        text,
    )

    # ---------------------------------------------------------
    # Plus notation
    #
    # "1+ years" -> 1
    # "2+ years" -> 2
    # ---------------------------------------------------------

    plus_pattern = (
        r"\b(\d+)\s*\+\s*"
        r"(?:years?|yrs?)"
        r"(?:\s+(?:of\s+)?(?:professional\s+|work\s+)?experience)\b"
    )

    plus_matches = re.findall(
        plus_pattern,
        text_without_ranges,
    )

    for value in plus_matches:
        requirements.append(
            int(value)
        )

    # Remove plus expressions before standard matching.
    text_without_plus = re.sub(
        plus_pattern,
        " ",
        text_without_ranges,
    )

    # ---------------------------------------------------------
    # Standard experience phrases
    #
    # "1 year of experience"
    # "2 years experience"
    # "3 years of professional experience"
    # ---------------------------------------------------------

    simple_pattern = (
        r"\b(\d+)\s*"
        r"(?:years?|yrs?)"
        r"(?:\s+of)?\s+"
        r"(?:professional\s+|work\s+)?experience\b"
    )

    simple_matches = re.findall(
        simple_pattern,
        text_without_plus,
    )

    for value in simple_matches:
        requirements.append(
            int(value)
        )

    # ---------------------------------------------------------
    # Minimum / at least
    #
    # "minimum 2 years experience" -> 2
    # "at least 3 years of professional experience" -> 3
    # ---------------------------------------------------------

    minimum_pattern = (
        r"\b(?:minimum|at least)\s+"
        r"(?:of\s+)?(\d+)\s*"
        r"(?:years?|yrs?)"
        r"(?:\s+of\s+(?:professional\s+|work\s+)?)?"
        r"\s+experience\b"
    )

    minimum_matches = re.findall(
        minimum_pattern,
        text_without_plus,
    )

    for value in minimum_matches:
        requirements.append(
            int(value)
        )

    if not requirements:
        return None

    return max(requirements)

# =========================================================
# Senior title detection
# =========================================================

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
        "vice president",
        "vp ",
    ]

    return any(
        keyword in title
        for keyword in senior_keywords
    )


# =========================================================
# Deterministic job facts
# =========================================================

def get_job_facts(job):

    title = job["title"].lower().strip()
    location = job["location"].lower().strip()
    description = job["description"].lower()

    combined = f"{title}\n{description}"

    # ---------------------------------------------------------
    # Internship
    # ---------------------------------------------------------

    is_internship = bool(
        re.search(
            r"\bintern\b|\binternship\b",
            title,
        )
    )

    # ---------------------------------------------------------
    # Employment type
    # ---------------------------------------------------------

    full_time_match = bool(
        re.search(
            r"\bfull[- ]time\b",
            combined,
        )
    )

    part_time_match = bool(
        re.search(
            r"\bpart[- ]time\b",
            combined,
        )
    )

    contract_match = bool(
        re.search(
            r"\bcontract\b|\bcontractor\b",
            combined,
        )
    )

    if is_internship:
        employment_type = "Internship"

    elif full_time_match:
        employment_type = "Full-time"

    elif part_time_match:
        employment_type = "Part-time"

    elif contract_match:
        employment_type = "Contract"

    else:
        employment_type = "Full-time"

    # ---------------------------------------------------------
    # Experience
    # ---------------------------------------------------------

    years_required = extract_experience_requirement(
        combined
    )

    # ---------------------------------------------------------
    # Seniority
    # ---------------------------------------------------------

    if is_internship:
        seniority_level = "Intern"

    elif is_senior_title(title):
        seniority_level = "Senior"

    elif (
        years_required is not None
        and years_required >= 5
    ):
        seniority_level = "Senior"

    elif (
        years_required is not None
        and years_required >= 2
    ):
        seniority_level = "Mid-level"

    elif re.search(
        r"\b(mid[- ]level|mid)\b",
        combined,
    ):
        seniority_level = "Mid-level"

    elif re.search(
        r"\b(junior|jr\.?|entry[- ]level|associate)\b",
        title,
    ):
        seniority_level = "Entry-level"

    else:
        seniority_level = "Unknown"

    # ---------------------------------------------------------
    # Previous internship
    # ---------------------------------------------------------

    requires_previous_internship = bool(
        re.search(
            r"\bprevious internships?\b"
            r"|\bprior internships?\b"
            r"|\bprevious internship experience\b"
            r"|\bprior internship experience\b",
            combined,
        )
    )

    # ---------------------------------------------------------
    # Education
    # ---------------------------------------------------------

    requires_cs_degree = bool(
        re.search(
            r"\bcomputer science\b"
            r"|\bcomputer engineering\b"
            r"|\bcomputer science degree\b"
            r"|\bcs degree\b",
            combined,
        )
    )

    # ---------------------------------------------------------
    # Programming
    # ---------------------------------------------------------

    requires_programming = bool(
        re.search(
            r"\bprogramming\b"
            r"|\bprogramming languages?\b"
            r"|\bsoftware development\b"
            r"|\bsoftware engineering\b"
            r"|\bcoding\b",
            combined,
        )
    )

    # ---------------------------------------------------------
    # Location
    # ---------------------------------------------------------

    india_cities = [
        "india",
        "bengaluru",
        "bangalore",
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

    india_job = any(
        city in location
        for city in india_cities
    )

    us_job = (
        "us - remote" in location
        or "us-remote" in location
        or "united states" in location
        or "usa" in location
    )

    canada_job = (
        "canada" in location
        or "canada-remote" in location
    )

    remote_job = "remote" in location

    return {
        "is_internship": is_internship,

        "employment_type": employment_type,

        "seniority_level": seniority_level,

        "years_required": years_required,

        "requires_previous_internship": (
            requires_previous_internship
        ),

        "requires_cs_degree": (
            requires_cs_degree
        ),

        "requires_programming": (
            requires_programming
        ),

        "india_job": india_job,

        "us_job": us_job,

        "canada_job": canada_job,

        "remote_job": remote_job,

        "location": location,
    }


# =========================================================
# Deterministic location matching
# =========================================================

def determine_location_match(profile, job_facts):

    preferred_locations = [
        str(location).lower().strip()
        for location in profile.get(
            "preferred_locations",
            [],
        )
    ]

    # ---------------------------------------------------------
    # Unsupported countries
    # ---------------------------------------------------------

    if job_facts["us_job"]:
        return False

    if job_facts["canada_job"]:
        return False

    # ---------------------------------------------------------
    # India
    # ---------------------------------------------------------

    if job_facts["india_job"]:

        if "india" in preferred_locations:
            return True

        return False

    # ---------------------------------------------------------
    # Generic remote
    # ---------------------------------------------------------

    if job_facts["remote_job"]:

        foreign_remote_locations = [
            "brazil",
            "singapore",
            "israel",
            "uk",
            "united kingdom",
            "europe",
            "australia",
            "germany",
            "france",
            "ireland",
            "netherlands",
            "canada",
            "usa",
            "united states",
        ]

        location = job_facts["location"]

        if any(
            country in location
            for country in foreign_remote_locations
        ):
            return False

        if "remote" in preferred_locations:
            return True

    return False


# =========================================================
# Result normalization
# =========================================================

def normalize_result(result):

    if not isinstance(result, dict):
        raise ValueError(
            "AI response was not a JSON object."
        )

    try:
        score = int(
            result.get(
                "match_score",
                0,
            )
        )

    except (TypeError, ValueError):
        score = 0

    result["match_score"] = max(
        0,
        min(100, score),
    )

    recommendation = str(
        result.get(
            "recommendation",
            "REVIEW",
        )
    ).upper().strip()

    if recommendation not in {
        "APPLY",
        "REVIEW",
        "SKIP",
    }:
        recommendation = "REVIEW"

    result["recommendation"] = recommendation

    list_fields = [
        "minimum_requirements_met",
        "minimum_requirements_missing",
        "preferred_matches",
        "preferred_missing",
        "strong_matches",
        "concerns",
    ]

    for field in list_fields:

        value = result.get(field)

        if not isinstance(value, list):
            result[field] = []

    result["reason"] = str(
        result.get(
            "reason",
            "",
        )
    ).strip()

    return result


# =========================================================
# Clean unsupported AI concerns
# =========================================================

def clean_ai_concerns(
    result,
    candidate_facts,
    job_facts,
):
    """
    Clean unsupported or factually incorrect AI output.

    Deterministic candidate facts take precedence over
    Ollama's interpretation.
    """

    concerns = result.get(
        "concerns",
        [],
    )

    cleaned = []

    unsupported_patterns = [
        r"company'?s culture",
        r"company culture",
        r"may not align with.*culture",
        r"large tech company",
        r"big tech company",
        r"may be less than expected",
        r"less than expected for",
        r"expected.*experience",
        r"may not fit.*culture",
        r"culture and expectations",
        r"team.*culture",
        r"what the company expects",
    ]

    unsupported_seniority_patterns = [
        r"may\s+imply\s+(?:a\s+)?more\s+senior\s+role",
        r"may\s+imply\s+(?:a\s+)?senior\s+role",
        r"might\s+imply\s+(?:a\s+)?more\s+senior\s+role",
        r"might\s+imply\s+(?:a\s+)?senior\s+role",
        r"could\s+imply\s+(?:a\s+)?more\s+senior\s+role",
        r"could\s+imply\s+(?:a\s+)?senior\s+role",
        r"title\s+.*may\s+imply.*senior",
        r"title\s+.*might\s+imply.*senior",
        r"title\s+.*could\s+imply.*senior",
    ]

    for concern in concerns:

        concern_text = str(
            concern
        ).strip()

        if not concern_text:
            continue
                # The deterministic title parser is authoritative.
        # Do not keep AI speculation that a normal title may
        # imply seniority when the actual title is not senior.
        if job_facts["seniority_level"] != "Senior":

            speculative_seniority = any(
                re.search(
                    pattern,
                    concern_text,
                    flags=re.IGNORECASE,
                )
                for pattern in unsupported_seniority_patterns
            )

            if speculative_seniority:
                continue

        satisfied_requirement = re.search(
            r"(?:which|that)\s+the\s+candidate\s+"
            r"(?:has|meets?|possesses|satisf(?:y|ies|ied))",
            concern_text,
            flags=re.IGNORECASE,
        )

        if satisfied_requirement:
            continue

        unsupported = any(
            re.search(
                pattern,
                concern_text,
                flags=re.IGNORECASE,
            )
            for pattern in unsupported_patterns
        )

        if unsupported:
            continue

        if candidate_facts["has_cs_education"]:

            education_patterns = [
                r"lack(?:s|ing)?\s+(?:of\s+)?(?:a\s+)?(?:formal\s+)?degree",
                r"missing\s+(?:a\s+)?(?:formal\s+)?degree",
                r"no\s+(?:formal\s+)?degree",
                r"without\s+(?:a\s+)?(?:formal\s+)?degree",
                r"does\s+not\s+have\s+(?:a\s+)?(?:formal\s+)?degree",
                r"doesn't\s+have\s+(?:a\s+)?(?:formal\s+)?degree",
                r"lack(?:s|ing)?\s+(?:of\s+)?(?:a\s+)?computer\s+science\s+degree",
                r"missing\s+(?:a\s+)?computer\s+science\s+degree",
                r"no\s+(?:formal\s+)?computer\s+science\s+degree",
                r"without\s+(?:a\s+)?computer\s+science\s+degree",
                r"does\s+not\s+have\s+(?:a\s+)?computer\s+science\s+degree",
                r"doesn't\s+have\s+(?:a\s+)?computer\s+science\s+degree",
                r"lack(?:s|ing)?\s+(?:of\s+)?(?:a\s+)?formal\s+education",
                r"missing\s+(?:a\s+)?formal\s+education",
                r"formal\s+education\s+requirement",
                r"education\s+requirement",
            ]

            education_concern = any(
                re.search(
                    pattern,
                    concern_text,
                    flags=re.IGNORECASE,
                )
                for pattern in education_patterns
            )

            if education_concern:
                continue

        education_duration_match = re.search(
            r"(?:at\s+least|minimum(?:\s+of)?)"
            r"\s*(\d+)"
            r"\s*(?:year|years)"
            r"\s+of\s+"
            r"(?:university|college|undergraduate|academic|education)",
            concern_text,
            flags=re.IGNORECASE,
        )

        if education_duration_match:

            required_years = int(
                education_duration_match.group(1)
            )

            if (
                candidate_facts["education_years"]
                >= required_years
            ):
                continue

        cleaned.append(
            concern_text
        )

    # ---------------------------------------------------------
    # Clean false minimum education requirements.
    # ---------------------------------------------------------

    minimum_missing = result.get(
        "minimum_requirements_missing",
        [],
    )

    if not isinstance(minimum_missing, list):
        minimum_missing = []

    filtered_minimum_missing = []

    for item in minimum_missing:

        text = str(item).strip()
        lower_text = text.lower()

        if candidate_facts["has_cs_education"]:

            if (
                "computer science" in lower_text
                or "cs degree" in lower_text
                or "computer engineering" in lower_text
            ):
                continue

            if (
                "bachelor" in lower_text
                and "degree" in lower_text
                and not any(
                    field in lower_text
                    for field in [
                        "electrical",
                        "mechanical",
                        "civil",
                        "chemical",
                        "electronics",
                        "telecommunications",
                        "finance",
                        "accounting",
                        "law",
                        "medicine",
                    ]
                )
            ):
                continue

        filtered_minimum_missing.append(item)

    result["minimum_requirements_missing"] = (
        filtered_minimum_missing
    )

    # ---------------------------------------------------------
    # Clean false preferred education requirements.
    # ---------------------------------------------------------

    preferred_missing = result.get(
        "preferred_missing",
        [],
    )

    if not isinstance(preferred_missing, list):
        preferred_missing = []

    filtered_preferred_missing = []

    for item in preferred_missing:

        text = str(item).strip()
        lower_text = text.lower()

        if candidate_facts["has_cs_education"]:

    # A combined bachelor's requirement such as:
    #
    # "Bachelor's in Computer Science, Design Engineering,
    # Human-Computer Interaction, or a related field
    # (Masters preferred)"
    #
    # is satisfied by the candidate's verified CS degree.
    # Preserve only the genuinely missing master's preference.
            if (
                "bachelor" in lower_text
                and (
                    "computer science" in lower_text
                    or "cs degree" in lower_text
                )
            ):
                if (
                    "master" in lower_text
                    or "masters" in lower_text
                    or "master's" in lower_text
                    or "postgraduate" in lower_text
                ):
                    filtered_preferred_missing.append(
                        "Master's degree preferred"
                    )

                continue

            # Generic bachelor's requirements are satisfied
            # by the verified Computer Science degree.
            if (
                "bachelor" in lower_text
                and "degree" in lower_text
                and not any(
                    field in lower_text
                    for field in [
                        "electrical",
                        "mechanical",
                        "civil",
                        "chemical",
                        "electronics",
                        "telecommunications",
                        "finance",
                        "accounting",
                        "law",
                        "medicine",
                    ]
                )
            ):
                continue

            # Explicit Computer Science education is satisfied.
            if (
                "computer science" in lower_text
                or "cs degree" in lower_text
            ):
                if (
                    "master" in lower_text
                    or "masters" in lower_text
                    or "master's" in lower_text
                ):
                    filtered_preferred_missing.append(
                        "Master's degree preferred"
                    )

                continue

        education_duration_match = re.search(
            r"(?:at\s+least|minimum(?:\s+of)?|requires?\s+at\s+least)"
            r"\s*(\d+)\s*(?:year|years)\s+of\s+"
            r"(?:university|college|undergraduate|academic|education)",
            lower_text,
        )

        if education_duration_match:

            required_years = int(
                education_duration_match.group(1)
            )

            if (
                candidate_facts["education_years"]
                >= required_years
            ):
                continue

        if (
            "university education" in lower_text
            and candidate_facts["has_education"]
        ):
            continue

        if (
            "college education" in lower_text
            and candidate_facts["has_education"]
        ):
            continue

        if (
            "undergraduate education" in lower_text
            and candidate_facts["has_education"]
        ):
            continue

        filtered_preferred_missing.append(item)

    result["preferred_missing"] = list(
        dict.fromkeys(
            filtered_preferred_missing
        )
    )

    result["concerns"] = cleaned

        # ---------------------------------------------------------
    # Clean false education claims from AI reason.
    # ---------------------------------------------------------

    reason = str(
        result.get(
            "reason",
            "",
        )
    ).strip()

    if candidate_facts["has_cs_education"]:

        # The AI may describe the verified CS education in many
        # different ways. Convert unsupported negative claims
        # into a factual statement.
        false_education_patterns = [
            # General degree claims
            r"lack(?:s|ing)?\s+(?:the\s+)?(?:necessary\s+|required\s+|relevant\s+|formal\s+)?degree",
            r"missing\s+(?:the\s+)?(?:necessary\s+|required\s+|relevant\s+|formal\s+)?degree",
            r"no\s+(?:formal\s+)?degree",
            r"without\s+(?:a\s+)?(?:formal\s+)?degree",
            r"does\s+not\s+have\s+(?:a\s+)?(?:formal\s+)?degree",
            r"doesn't\s+have\s+(?:a\s+)?(?:formal\s+)?degree",

            # Computer Science degree claims
            r"lack(?:s|ing)?\s+(?:the\s+)?(?:necessary\s+|required\s+|relevant\s+)?computer\s+science\s+degree",
            r"missing\s+(?:the\s+)?(?:necessary\s+|required\s+|relevant\s+)?computer\s+science\s+degree",
            r"no\s+(?:formal\s+)?computer\s+science\s+degree",
            r"without\s+(?:a\s+)?computer\s+science\s+degree",
            r"does\s+not\s+have\s+(?:a\s+)?computer\s+science\s+degree",
            r"doesn't\s+have\s+(?:a\s+)?computer\s+science\s+degree",

            # Computer Science education claims
            r"lack(?:s|ing)?\s+(?:the\s+)?(?:necessary\s+|required\s+|relevant\s+)?computer\s+science\s+education",
            r"missing\s+(?:the\s+)?(?:necessary\s+|required\s+|relevant\s+)?computer\s+science\s+education",
            r"no\s+(?:formal\s+)?computer\s+science\s+education",
            r"without\s+(?:a\s+)?computer\s+science\s+education",
            r"does\s+not\s+have\s+(?:a\s+)?(?:formal\s+)?computer\s+science\s+education",
            r"doesn't\s+have\s+(?:a\s+)?(?:formal\s+)?computer\s+science\s+education",
        ]

        for pattern in false_education_patterns:

            reason = re.sub(
                pattern,
                "has verified Computer Science education",
                reason,
                flags=re.IGNORECASE,
            )

        # Catch sentence-level formulations such as:
        # "The candidate lacks the necessary Computer Science
        # education."
        reason = re.sub(
            r"the\s+candidate\s+"
            r"(?:lacks?|is\s+lacking|is\s+missing|does\s+not\s+have|"
            r"doesn't\s+have)\s+"
            r"(?:the\s+)?(?:necessary\s+|required\s+|relevant\s+)?"
            r"computer\s+science\s+(?:education|degree)",
            "the candidate has verified Computer Science education",
            reason,
            flags=re.IGNORECASE,
        )

        # Catch broader negative formal-degree statements.
        reason = re.sub(
            r"the\s+candidate\s+"
            r"(?:lacks?|is\s+lacking|is\s+missing|does\s+not\s+have|"
            r"doesn't\s+have)\s+"
            r"(?:a\s+)?(?:formal\s+)?degree",
            "the candidate has a verified Computer Science degree",
            reason,
            flags=re.IGNORECASE,
        )

    result["reason"] = reason

    return result

# =========================================================
# Internship deterministic rules
# =========================================================

def enforce_internship_rules(
    result,
    candidate_facts,
    job_facts,
):
    """
    Apply deterministic evidence for internships.

    This prevents Ollama from incorrectly saying that the
    candidate has no internship/project/CS evidence.
    """

    if not job_facts["is_internship"]:
        return result

    result["seniority_level"] = "Intern"
    result["employment_type"] = "Internship"

    # ---------------------------------------------------------
    # Build deterministic evidence
    # ---------------------------------------------------------

    evidence = 0

    if candidate_facts["has_cs_education"]:
        evidence += 25

    elif candidate_facts["has_education"]:
        evidence += 15

    if candidate_facts["has_programming_skills"]:
        evidence += 25

    if candidate_facts["has_projects"]:
        evidence += 20

    if candidate_facts["has_internship_experience"]:
        evidence += 20

    evidence = min(
        evidence,
        100,
    )

    # ---------------------------------------------------------
    # Add deterministic strengths
    # ---------------------------------------------------------

    strong_matches = result.get(
        "strong_matches",
        [],
    )

    if candidate_facts["has_cs_education"]:
        strong_matches.append(
            "Computer Science education"
        )

    if candidate_facts["has_programming_skills"]:
        strong_matches.append(
            "Programming experience through listed skills"
        )

    if candidate_facts["has_projects"]:
        strong_matches.append(
            "Relevant software projects"
        )

    if candidate_facts["has_internship_experience"]:
        strong_matches.append(
            "Previous internship experience"
        )

    result["strong_matches"] = list(
        dict.fromkeys(
            strong_matches
        )
    )

    # ---------------------------------------------------------
    # Do not allow AI to invent an education gap
    # ---------------------------------------------------------

    missing = result.get(
        "minimum_requirements_missing",
        [],
    )

    if candidate_facts["has_cs_education"]:

        filtered_missing = []

        for item in missing:

            text = str(item).lower()

            if (
                "computer science" in text
                or "cs degree" in text
                or "computer engineering" in text
                or "university education" in text
                or "degree" in text
            ):
                continue

            filtered_missing.append(item)

        result["minimum_requirements_missing"] = (
            filtered_missing
        )

        # ---------------------------------------------------------
    # Do not allow AI to invent a preferred education gap
    # ---------------------------------------------------------

    preferred_missing = result.get(
        "preferred_missing",
        [],
    )

    filtered_preferred_missing = []

    for item in preferred_missing:

        text = str(item).lower()

        education_requirement = re.search(
            r"(?:at\s+least|minimum(?:\s+of)?|requires?\s+at\s+least)"
            r"\s*(\d+)"
            r"\s*(?:year|years)"
            r"\s+of\s+"
            r"(?:university|college|undergraduate|academic|education)",
            text,
        )

        if education_requirement:

            required_years = int(
                education_requirement.group(1)
            )

            if (
                candidate_facts["education_years"]
                >= required_years
            ):
                continue

        if (
            "university education" in text
            and candidate_facts["has_education"]
        ):
            continue

        if (
            "college education" in text
            and candidate_facts["has_education"]
        ):
            continue

        if (
            "undergraduate education" in text
            and candidate_facts["has_education"]
        ):
            continue

        filtered_preferred_missing.append(item)

    result["preferred_missing"] = (
        filtered_preferred_missing
    )

    # ---------------------------------------------------------
    # Internship score floor
    # ---------------------------------------------------------

    if evidence >= 75:

        result["match_score"] = max(
            result.get(
                "match_score",
                0,
            ),
            75,
        )

    elif evidence >= 60:

        result["match_score"] = max(
            result.get(
                "match_score",
                0,
            ),
            65,
        )

    # ---------------------------------------------------------
    # If all hard internship requirements are satisfied,
    # allow APPLY.
    # ---------------------------------------------------------

    if (
        result["match_score"] >= 75
        and not result.get(
            "minimum_requirements_missing"
        )
        and result.get(
            "location_match",
            False,
        )
    ):
        result["recommendation"] = "APPLY"

    # ---------------------------------------------------------
    # Recommendation / score consistency
    # ---------------------------------------------------------

    if (
        result.get("recommendation") == "APPLY"
        and result.get("match_score", 0) < 75
    ):
        result["recommendation"] = "REVIEW"

        result["reason"] = (
            "REVIEW: the match score is below the minimum "
            "threshold required for APPLY."
        )

        result["concerns"] = [
            *result.get("concerns", []),
            "Consistency rule: APPLY requires a match score of at least 75.",
        ]

    return result


# =========================================================
# HARD EXPERIENCE RULE
# =========================================================

def enforce_maximum_one_year_rule(
    result,
    profile,
    job_facts,
):
    """
    ABSOLUTE RULE:

    APPLY is allowed only when the explicit professional
    experience requirement is definitely <= 1 year.
    """

    years_required = job_facts[
        "years_required"
    ]

    if years_required is None:
        return result

    if years_required <= MAX_EXPERIENCE_YEARS:
        return result

    result["recommendation"] = "SKIP"
    result["match_score"] = 0

    candidate_years = profile.get(
        "years_of_experience",
        0,
    )

    result["concerns"] = [
        (
            "Hard rule: this agent only applies to jobs "
            "requiring 0-1 years of professional experience. "
            f"This job requires {years_required} years or more. "
            f"The candidate profile lists {candidate_years} years."
        )
    ]

    result["reason"] = (
        "SKIP: the job requires more than 1 year "
        "of professional experience. The maximum allowed "
        "experience requirement for APPLY is 1 year."
    )

    return result


# =========================================================
# HARD APPLY SAFETY RULES
# =========================================================

def enforce_apply_safety_rules(
    result,
    profile,
    job_facts,
):
    """
    Final deterministic authority.

    Ollama can recommend APPLY, but it cannot override
    verified candidate facts or hard eligibility rules.
    """

    # ---------------------------------------------------------
    # Candidate facts
    # ---------------------------------------------------------

    candidate_facts = get_candidate_facts(
        profile
    )

    # ---------------------------------------------------------
    # Minimum requirements
    # ---------------------------------------------------------

    minimum_missing = result.get(
        "minimum_requirements_missing",
        [],
    )

    if not isinstance(minimum_missing, list):
        minimum_missing = []

    cleaned_minimum_missing = []

    for item in minimum_missing:

        text = str(item).strip()

        if not text:
            continue

        lower_text = text.lower()

        # -----------------------------------------------------
        # Verified Computer Science education
        # -----------------------------------------------------

        if candidate_facts["has_cs_education"]:

            if (
                "computer science" in lower_text
                and any(
                    keyword in lower_text
                    for keyword in [
                        "degree",
                        "education",
                        "bachelor",
                        "bachelors",
                        "bachelor's",
                        "cs degree",
                    ]
                )
            ):
                continue

            if (
                "cs degree" in lower_text
            ):
                continue

        # -----------------------------------------------------
        # Verified general education
        # -----------------------------------------------------

        if candidate_facts["has_education"]:

            if (
                "university education" in lower_text
                or "college education" in lower_text
                or "undergraduate education" in lower_text
            ):
                continue

        cleaned_minimum_missing.append(
            text
        )

    result["minimum_requirements_missing"] = (
        list(
            dict.fromkeys(
                cleaned_minimum_missing
            )
        )
    )

    # If genuine minimum requirements are missing,
    # APPLY is never allowed.
    if cleaned_minimum_missing:

        result["recommendation"] = "SKIP"
        result["match_score"] = 0

        result["reason"] = (
            "SKIP: one or more stated minimum job "
            "requirements are not satisfied."
        )

        result["concerns"] = [
            *result.get("concerns", []),
            "Hard rule: minimum job requirements are missing.",
        ]

        return result

    # ---------------------------------------------------------
    # Location
    # ---------------------------------------------------------

    if not result.get(
        "location_match",
        False,
    ):

        result["recommendation"] = "SKIP"
        result["match_score"] = 0

        result["reason"] = (
            "SKIP: the job location does not match "
            "the candidate's allowed locations."
        )

        return result

    # ---------------------------------------------------------
    # Experience
    # ---------------------------------------------------------

    years_required = job_facts[
        "years_required"
    ]

    if (
        years_required is not None
        and years_required > MAX_EXPERIENCE_YEARS
    ):

        return enforce_maximum_one_year_rule(
            result,
            profile,
            job_facts,
        )

    # ---------------------------------------------------------
    # Senior title
    # ---------------------------------------------------------

    if job_facts[
        "seniority_level"
    ] == "Senior":

        result["recommendation"] = "SKIP"
        result["match_score"] = 0

        result["reason"] = (
            "SKIP: the job is above the candidate's "
            "target seniority level."
        )

        return result

    # ---------------------------------------------------------
    # Final APPLY score consistency
    # ---------------------------------------------------------

    if (
        result.get("recommendation") == "APPLY"
        and result.get("match_score", 0) < 75
    ):
        result["match_score"] = 75

    return result


# =========================================================
# AI matching
# =========================================================

def match_job(job, profile):

    candidate_facts = get_candidate_facts(
        profile
    )

    job_facts = get_job_facts(
        job
    )

    location_match = determine_location_match(
        profile,
        job_facts,
    )

    # ---------------------------------------------------------
    # HARD EXPERIENCE SAFETY BEFORE AI
    # ---------------------------------------------------------

    if (
        job_facts["years_required"] is not None
        and job_facts["years_required"] > MAX_EXPERIENCE_YEARS
    ):

        result = {
            "match_score": 0,
            "recommendation": "SKIP",
            "seniority_level": job_facts["seniority_level"],
            "employment_type": job_facts["employment_type"],
            "location_match": location_match,
            "minimum_requirements_met": [],
            "minimum_requirements_missing": [],
            "preferred_matches": [],
            "preferred_missing": [],
            "strong_matches": [],
            "concerns": [],
            "reason": "",
        }

        return enforce_maximum_one_year_rule(
            result,
            profile,
            job_facts,
        )

    # ---------------------------------------------------------
    # Senior safety before Ollama
    # ---------------------------------------------------------

    if job_facts["seniority_level"] == "Senior":

        return {
            "match_score": 0,
            "recommendation": "SKIP",
            "seniority_level": job_facts["seniority_level"],
            "employment_type": job_facts["employment_type"],
            "location_match": location_match,
            "minimum_requirements_met": [],
            "minimum_requirements_missing": [],
            "preferred_matches": [],
            "preferred_missing": [],
            "strong_matches": [],
            "concerns": [
                "Hard rule: senior-level roles are not eligible for APPLY."
            ],
            "reason": (
                "SKIP: senior-level roles are outside "
                "the candidate's 0-1 year application target."
            ),
        }

    # ---------------------------------------------------------
    # Candidate skill summary
    # ---------------------------------------------------------

    candidate_skills = ", ".join(
        sorted(
            candidate_facts["skills"]
        )
    )

    # ---------------------------------------------------------
    # AI prompt
    # ---------------------------------------------------------

    prompt = f"""
You are a strict job-matching engine.

Evaluate whether this candidate should apply to this job.

Use ONLY the candidate facts supplied below.

Never invent:
- skills
- experience
- education
- projects
- certifications
- work authorization
- achievements

IMPORTANT EXPERIENCE RULE:

The field "Explicit professional experience requirement"
contains ONLY professional/work experience requirements.

Do NOT interpret:
- years of university education
- years of college
- years of undergraduate study
- years of academic study
- years of education
- university education duration

as professional work experience.

For example:

"At least 1 year of university education"
does NOT mean
"1 year of professional work experience."

Also distinguish between MINIMUM requirements and PREFERRED qualifications.

A preferred qualification is NOT a minimum requirement.

============================================================
CANDIDATE FACTS
============================================================

Years of professional experience:
{candidate_facts["years_of_experience"]}

Current location:
{candidate_facts["current_location"]}

Preferred locations:
{candidate_facts["preferred_locations"]}

Computer Science education:
{candidate_facts["has_cs_education"]}

Education exists:
{candidate_facts["has_education"]}

Previous internship experience:
{candidate_facts["has_internship_experience"]}

Number of internships:
{candidate_facts["internship_count"]}

Projects:
{candidate_facts["has_projects"]}

Programming skills:
{candidate_facts["has_programming_skills"]}

Candidate skills:
{candidate_skills}

============================================================
DETERMINISTIC JOB FACTS
============================================================

Job title:
{job["title"]}

Company:
{job["company"]}

Location:
{job["location"]}

Internship:
{job_facts["is_internship"]}

Employment type:
{job_facts["employment_type"]}

Seniority:
{job_facts["seniority_level"]}

Explicit professional experience requirement:
{job_facts["years_required"]}

Requires previous internship:
{job_facts["requires_previous_internship"]}

Requires Computer Science degree:
{job_facts["requires_cs_degree"]}

Requires programming:
{job_facts["requires_programming"]}

Location match:
{location_match}

============================================================
HARD RULES
============================================================

1. The candidate has approximately 1 year of professional experience.

2. Jobs whose MINIMUM required professional experience is more than 1 year are NOT eligible.

3. For experience ranges, use the LOWER bound as the minimum requirement.
   Example: "1-2 years" means the minimum requirement is 1 year.
   Therefore, a candidate with approximately 1 year is eligible.

4. "1+ years" means a minimum requirement of 1 year.
   Therefore, a candidate with approximately 1 year is eligible.

5. "2+ years" means a minimum requirement of 2 years.
   Therefore, a candidate with approximately 1 year is NOT eligible.

6. Senior, Staff, Principal and Lead roles are NOT eligible.

7. If location_match is false, recommendation MUST be SKIP.

8. Computer Science education is TRUE.

9. The candidate has programming skills.

10. The candidate has software projects.

11. Previous internship experience is TRUE.

12. Do not claim the candidate lacks university education when
    Computer Science education is TRUE.

13. Do not claim the candidate lacks programming experience
    when programming skills or projects are TRUE.

14. For internships, relevant projects, programming skills,
    education and previous internships should be considered.

15. Distinguish MINIMUM requirements from PREFERRED qualifications.

16. A preferred qualification should be listed under
    "preferred_missing" if the candidate does not have it,
    NOT under "minimum_requirements_missing".

17. Do not convert university education duration into
    professional experience.

18. Do not treat "1 year of university education" as
    "1 year of work experience".

19. APPLY means the candidate appears genuinely qualified
    based on the stated requirements.

20. REVIEW means there is meaningful uncertainty.

21. SKIP means a clear requirement or hard rule fails.

22. Do not speculate about company culture.

23. Do not speculate about what the company "expects".

24. Return ONLY valid JSON.

============================================================
JOB DESCRIPTION
============================================================

{job["description"]}

============================================================
OUTPUT
============================================================

Return exactly this JSON structure:

{{
    "match_score": 0,
    "recommendation": "APPLY",
    "seniority_level": "{job_facts["seniority_level"]}",
    "employment_type": "{job_facts["employment_type"]}",
    "location_match": {str(location_match).lower()},
    "minimum_requirements_met": [],
    "minimum_requirements_missing": [],
    "preferred_matches": [],
    "preferred_missing": [],
    "strong_matches": [],
    "concerns": [],
    "reason": ""
}}
"""

    # ---------------------------------------------------------
    # Ask Ollama
    # ---------------------------------------------------------

    raw_result = ask_ai(
        prompt
    )

    result = extract_json(
        raw_result
    )

    result = normalize_result(
        result
    )

    # ---------------------------------------------------------
    # Deterministic facts override AI
    # ---------------------------------------------------------

    result["seniority_level"] = (
        job_facts["seniority_level"]
    )

    result["employment_type"] = (
        job_facts["employment_type"]
    )

    result["location_match"] = (
        location_match
    )

    # ---------------------------------------------------------
    # Clean AI output
    # ---------------------------------------------------------

    result = clean_ai_concerns(
        result,
        candidate_facts,
        job_facts,
    )

    # ---------------------------------------------------------
    # Internship evidence
    # ---------------------------------------------------------

    result = enforce_internship_rules(
        result,
        candidate_facts,
        job_facts,
    )

    # ---------------------------------------------------------
    # Maximum experience rule
    # ---------------------------------------------------------

    result = enforce_maximum_one_year_rule(
        result,
        profile,
        job_facts,
    )

    # ---------------------------------------------------------
    # Final safety rules
    # ---------------------------------------------------------

    result = enforce_apply_safety_rules(
        result,
        profile,
        job_facts,
    )

    # ---------------------------------------------------------
    # Final consistency
    # ---------------------------------------------------------

    if job_facts["is_internship"]:
        result["seniority_level"] = "Intern"
        result["employment_type"] = "Internship"

    return result


# =========================================================
# Save result
# =========================================================

def save_match(job_id, result):

    connection = get_connection()

    connection.execute(
        """
        UPDATE jobs
        SET
            match_score = ?,
            recommendation = ?,
            matched_at = datetime('now')
        WHERE id = ?
        """,
        (
            result["match_score"],
            result["recommendation"],
            job_id,
        ),
    )

    connection.commit()
    connection.close()


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    profile = load_profile()

    jobs = get_relevant_jobs()

    print()
    print(
        f"Jobs waiting for AI matching: {len(jobs)}"
    )
    print()

    if not jobs:
        print(
            "No new eligible jobs require AI matching."
        )

    for job in jobs:

        print("=" * 80)

        print(
            f"{job['company']} — {job['title']}"
        )

        print(
            f"Location: {job['location']}"
        )

        try:

            result = match_job(
                job,
                profile,
            )

            save_match(
                job["id"],
                result,
            )

            print(
                f"Score: {result['match_score']}"
            )

            print(
                f"Recommendation: "
                f"{result['recommendation']}"
            )

            print(
                f"Seniority: "
                f"{result['seniority_level']}"
            )

            print(
                f"Employment type: "
                f"{result['employment_type']}"
            )

            print(
                f"Location match: "
                f"{result['location_match']}"
            )

            print(
                f"Reason: "
                f"{result['reason']}"
            )

            if result.get(
                "minimum_requirements_missing"
            ):

                print(
                    "Missing minimum requirements: "
                    f"{result['minimum_requirements_missing']}"
                )

            if result.get(
                "preferred_missing"
            ):

                print(
                    "Missing preferred qualifications: "
                    f"{result['preferred_missing']}"
                )

            if result.get(
                "concerns"
            ):

                print(
                    "Concerns: "
                    f"{result['concerns']}"
                )

        except Exception as error:

            print(
                f"AI matching failed: {error}"
            )

    print()
    print("Matching complete.")