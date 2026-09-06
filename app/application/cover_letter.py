import json
import re
from pathlib import Path

import requests

from app.database.db import get_connection


BASE_DIR = Path(__file__).resolve().parents[2]

PROFILE_FILE = BASE_DIR / "data" / "profile.json"

COVER_LETTERS_DIR = (
    BASE_DIR
    / "data"
    / "applications"
    / "cover_letters"
)

COVER_LETTER_MODEL = "qwen2.5:7b"

OLLAMA_URL = "http://localhost:11434/api/generate"


# Phrases that tend to produce generic or exaggerated letters.
FORBIDDEN_PHRASES = [
    "passionate",
    "detail-oriented",
    "cutting-edge",
    "industry-leading",
    "revolutionary",
    "world-class",
    "perfect fit",
    "ideal candidate",
    "dream candidate",
    "excited to join",
    "excited about the opportunity",
    "thrilled to join",
    "thrilled to apply",
    "enthusiastic about joining",
    "passionate about your mission",
    "innovative solutions",
    "innovative technology",
    "state-of-the-art",
    "highly experienced",
    "extensively experienced",
    "seasoned developer",
    "seasoned professional",
]


# Phrases that commonly indicate unsupported claims or model padding.
SUSPICIOUS_PHRASES = [
    "significantly improved",
    "substantially improved",
    "dramatically improved",
    "greatly improved",
    "markedly improved",
    "significantly enhanced",
    "substantially enhanced",
    "dramatically enhanced",
    "greatly enhanced",
    "markedly enhanced",
    "significantly increased",
    "substantially increased",
    "dramatically increased",
    "greatly increased",
    "markedly increased",
    "significantly reduced",
    "substantially reduced",
    "dramatically reduced",
    "greatly reduced",
    "markedly reduced",
    "significant impact",
    "substantial impact",
    "major impact",
    "measurable impact",
    "proven track record",
    "strong track record",
    "demonstrated my ability to",
    "showcased my ability to",
    "honed my ability to",
    "made a significant impact",
    "drive meaningful impact",
    "deliver exceptional",
    "deliver outstanding",
    "high-performing applications",
    "high-performing systems",
    "high-performing solutions",
    "robust and scalable",
    "scalable and performant",
]

UNSUPPORTED_RESULT_PATTERNS = [
    r"\bsignificantly\b.{0,80}\b(improv|enhanc|increas|reduc)",
    r"\bsubstantially\b.{0,80}\b(improv|enhanc|increas|reduc)",
    r"\bdramatically\b.{0,80}\b(improv|enhanc|increas|reduc)",
    r"\bgreatly\b.{0,80}\b(improv|enhanc|increas|reduc)",
    r"\bmarkedly\b.{0,80}\b(improv|enhanc|increas|reduc)",
    r"\b(measurably|measurable)\b.{0,80}\b(improv|enhanc|increas|reduc)",
    r"\b(high[- ]performing)\b",
    r"\b(exceptional|outstanding)\s+(results|performance|solutions|applications)",
]


def load_profile():
    with PROFILE_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "profile.json must contain a JSON object."
        )

    return data


def ask_cover_letter_ai(prompt: str) -> str:
    """
    Generate a fresh cover letter using the local Qwen model.

    This model is intentionally separate from the job matcher.
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": COVER_LETTER_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.85,
                "num_predict": 500,
            },
        },
        timeout=600,
    )

    response.raise_for_status()

    data = response.json()

    final_response = data.get("response")

    if isinstance(final_response, str):
        final_response = final_response.strip()

    if final_response:
        return final_response

    raise ValueError(
        "The cover-letter model returned an empty response. "
        f"Ollama response keys: {list(data.keys())}"
    )


def clean_cover_letter(text: str) -> str:
    """
    Remove common model formatting mistakes without rewriting
    the actual content.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove Markdown code fences.
    text = re.sub(
        r"^```(?:text|plaintext)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = text.strip()

    # Remove an accidental Subject line.
    text = re.sub(
        r"^subject\s*:\s*.*(?:\r?\n)+",
        "",
        text,
        count=1,
        flags=re.IGNORECASE,
    )

    # Remove common model preambles.
    preamble_patterns = [
        r"^here is (?:a|the) .*?cover letter.*?:\s*",
        r"^here's (?:a|the) .*?cover letter.*?:\s*",
        r"^cover letter:\s*",
        r"^final answer:\s*",
    ]

    for pattern in preamble_patterns:
        text = re.sub(
            pattern,
            "",
            text,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )

    # Remove a generated resume-style header if Qwen ignores
    # the instruction and produces one.
    header_patterns = [
        r"^\[Your Name\]\s*",
        r"^\[Your Address\]\s*",
        r"^\[City, State, ZIP Code\]\s*",
        r"^\[Email Address\]\s*",
        r"^\[Phone Number\]\s*",
        r"^\[Date\]\s*",
        r"^Hiring Manager\s*",
        r"^\[Company Address\]\s*",
        r"^\[Company Address\]\s*\n",
    ]

    for pattern in header_patterns:
        text = re.sub(
            pattern,
            "",
            text,
            count=1,
            flags=re.IGNORECASE,
        )

    # If the model somehow starts before the salutation,
    # retain the actual letter body.
    dear_match = re.search(
        r"\bDear Hiring Team,\s*",
        text,
        flags=re.IGNORECASE,
    )

    if dear_match:
        text = text[dear_match.start():]

    # Normalize excessive blank lines.
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    # Remove accidental surrounding quotes.
    if (
        len(text) >= 2
        and text.startswith('"')
        and text.endswith('"')
    ):
        text = text[1:-1].strip()

    return text.strip()


def normalize_for_matching(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.lower(),
    ).strip()


def phrase_present(
    text: str,
    phrase: str,
) -> bool:
    normalized_text = normalize_for_matching(text)
    normalized_phrase = normalize_for_matching(phrase)

    return normalized_phrase in normalized_text


def validate_no_placeholders(
    cover_letter: str,
) -> None:
    forbidden_patterns = [
        r"\[insert",
        r"\[your ",
        r"<your ",
        r"<insert",
        r"\bplaceholder\b",
        r"\bcompany name\b",
        r"\bjob title\b",
        r"\byour company\b",
        r"\[company\]",
        r"\[role\]",
        r"\[position\]",
        r"\[candidate\]",
        r"\[name\]",
        r"\[address\]",
        r"\[email\]",
        r"\[phone\]",
        r"\[date\]",
    ]

    for pattern in forbidden_patterns:
        if re.search(
            pattern,
            cover_letter,
            flags=re.IGNORECASE,
        ):
            raise ValueError(
                "The generated cover letter contains "
                f"an unresolved placeholder: {pattern}"
            )


def validate_no_model_meta(
    cover_letter: str,
) -> None:
    meta_patterns = [
        r"^here is",
        r"^here's",
        r"^sure[,!]",
        r"^certainly[,!]",
        r"^of course[,!]",
        r"^cover letter:",
        r"^final answer:",
        r"^below is",
        r"^here's a polished",
    ]

    for pattern in meta_patterns:
        if re.search(
            pattern,
            cover_letter,
            flags=re.IGNORECASE,
        ):
            raise ValueError(
                "The generated cover letter contains "
                "model meta-commentary."
            )


def validate_structure(
    cover_letter: str,
    profile: dict,
) -> None:
    if not cover_letter:
        raise ValueError(
            "The AI returned an empty cover letter."
        )

    if len(cover_letter) < 600:
        raise ValueError(
            "The generated cover letter is too short."
        )

    if len(cover_letter) > 3000:
        raise ValueError(
            "The generated cover letter is too long."
        )

    if not re.search(
        r"^Dear Hiring Team,",
        cover_letter,
        flags=re.IGNORECASE,
    ):
        raise ValueError(
            "The generated cover letter does not start "
            "with 'Dear Hiring Team,'."
        )

    expected_signature = (
        "Best regards,\n"
        "MD SAFI MAAZ"
    )

    if not cover_letter.rstrip().endswith(
        expected_signature
    ):
        raise ValueError(
            "The generated cover letter does not end with "
            "'Best regards, MD SAFI MAAZ'."
        )

    paragraph_blocks = [
        block.strip()
        for block in re.split(
            r"\n\s*\n",
            cover_letter.strip(),
        )
        if block.strip()
    ]

    if len(paragraph_blocks) != 4:
        raise ValueError(
            "The generated cover letter must contain "
            "exactly four paragraphs."
        )

    name = str(
        profile.get(
            "name",
            "",
        )
    ).strip()

    if name and name.lower() not in cover_letter.lower():
        raise ValueError(
            "The generated cover letter does not contain "
            "the candidate name."
        )


def validate_company_and_role(
    cover_letter: str,
    job: dict,
) -> None:
    company = str(
        job.get(
            "company",
            "",
        )
    ).strip()

    if company and company.lower() not in cover_letter.lower():
        raise ValueError(
            "The generated cover letter does not reference "
            f"the target company: {company}"
        )

    title = str(
        job.get(
            "title",
            "",
        )
    ).strip()

    if not title:
        return

    title_words = [
        word.lower()
        for word in re.findall(
            r"[A-Za-z0-9]+",
            title,
        )
        if len(word) >= 3
    ]

    if not title_words:
        return

    matching_words = sum(
        1
        for word in title_words
        if word in cover_letter.lower()
    )

    if matching_words == 0:
        raise ValueError(
            "The generated cover letter does not appear "
            "to reference the target role."
        )


def validate_forbidden_language(
    cover_letter: str,
) -> None:
    for phrase in FORBIDDEN_PHRASES:
        if phrase_present(
            cover_letter,
            phrase,
        ):
            raise ValueError(
                "The generated cover letter contains "
                f"generic or exaggerated wording: '{phrase}'."
            )


def validate_suspicious_language(
    cover_letter: str,
) -> None:
    for phrase in SUSPICIOUS_PHRASES:
        if phrase_present(
            cover_letter,
            phrase,
        ):
            raise ValueError(
                "The generated cover letter contains "
                f"potentially unsupported wording: '{phrase}'."
            )

def validate_unsupported_results(
    cover_letter: str,
) -> None:
    normalized = normalize_for_matching(
        cover_letter
    )

    for pattern in UNSUPPORTED_RESULT_PATTERNS:
        if re.search(
            pattern,
            normalized,
            flags=re.IGNORECASE,
        ):
            raise ValueError(
                "The generated cover letter contains "
                "an unsupported performance or outcome claim."
            )

def validate_no_resume_header(
    cover_letter: str,
) -> None:
    header_indicators = [
        "[your name]",
        "[your address]",
        "[city, state, zip code]",
        "[email address]",
        "[phone number]",
        "[date]",
        "hiring manager",
        "[company address]",
    ]

    normalized = normalize_for_matching(
        cover_letter
    )

    for indicator in header_indicators:
        if indicator in normalized:
            raise ValueError(
                "The generated cover letter contains "
                "a resume-style header."
            )

def validate_project_boundaries(
    cover_letter: str,
    profile: dict,
) -> None:
    """
    Prevent clear employer/project fact mixing.

    Validation is paragraph-aware so facts belonging to different
    employers can safely appear in different paragraphs.
    """

    paragraphs = [
        normalize_for_matching(block)
        for block in re.split(
            r"\n\s*\n",
            cover_letter.strip(),
        )
        if block.strip()
    ]

    # --------------------------------------------------------------
    # Employer/project association checks
    # --------------------------------------------------------------

    experience = profile.get(
        "experience",
        [],
    )

    projects = profile.get(
        "projects",
        [],
    )

    employer_names = [
        str(item.get("company", "")).strip()
        for item in experience
        if item.get("company")
    ]

    project_names = [
        str(item.get("name", "")).strip()
        for item in projects
        if item.get("name")
    ]

    for paragraph in paragraphs:
        for project_name in project_names:
            project = normalize_for_matching(
                project_name
            )

            if not project:
                continue

            if project not in paragraph:
                continue

            for employer_name in employer_names:
                employer = normalize_for_matching(
                    employer_name
                )

                if not employer:
                    continue

                if employer in paragraph:
                    raise ValueError(
                        "The generated cover letter appears "
                        f"to associate personal project "
                        f"'{project_name}' with employer "
                        f"'{employer_name}' in the same "
                        "paragraph."
                    )

    # --------------------------------------------------------------
    # Grievance management system belongs to Sparrow Softtech.
    #
    # Only reject it when IT FOSTERS is mentioned in the SAME
    # paragraph, which indicates an actual attribution problem.
    # --------------------------------------------------------------

    grievance_terms = [
        "grievance management system",
        "grievance system",
        "submitting and tracking grievances",
    ]

    it_fosters_names = [
        "it fosters web solutions pvt. ltd",
        "it fosters web solutions",
        "it fosters",
    ]

    sparrow_names = [
        "sparrow softtech pvt ltd",
        "sparrow softtech",
    ]

    for paragraph in paragraphs:
        contains_grievance = any(
            term in paragraph
            for term in grievance_terms
        )

        if not contains_grievance:
            continue

        if any(
            name in paragraph
            for name in it_fosters_names
        ):
            raise ValueError(
                "The generated cover letter appears to "
                "attribute the grievance management work "
                "to IT FOSTERS. That experience belongs "
                "to Sparrow Softtech."
            )

    # --------------------------------------------------------------
    # Redux Toolkit belongs to IT FOSTERS.
    #
    # Only reject it when Sparrow is mentioned in the same
    # paragraph.
    # --------------------------------------------------------------

    for paragraph in paragraphs:
        if "redux toolkit" not in paragraph:
            continue

        if any(
            name in paragraph
            for name in sparrow_names
        ):
            raise ValueError(
                "The generated cover letter appears to "
                "attribute Redux Toolkit experience to "
                "Sparrow Softtech."
            )

def validate_cover_letter(
    cover_letter: str,
    profile: dict,
    job: dict,
) -> None:
    """
    Conservative deterministic validation.

    The validator does not attempt to prove that every sentence
    is true. Instead, it rejects known unsafe patterns and
    obvious model failures before the letter is saved.
    """

    validate_structure(
        cover_letter,
        profile,
    )

    validate_no_placeholders(
        cover_letter,
    )

    validate_no_model_meta(
        cover_letter,
    )

    validate_no_resume_header(
        cover_letter,
    )

    validate_company_and_role(
        cover_letter,
        job,
    )

    validate_forbidden_language(
        cover_letter,
    )

    validate_suspicious_language(
        cover_letter,
    )

    validate_unsupported_results(
        cover_letter,
    )

    validate_project_boundaries(
        cover_letter,
        profile,
    )


def build_candidate_evidence(
    profile: dict,
) -> dict:
    """
    Create an explicit evidence packet.

    Employer experience and personal projects remain separate.
    """

    experience = []

    for item in profile.get(
        "experience",
        [],
    ):
        experience.append(
            {
                "company": item.get(
                    "company"
                ),
                "role": item.get(
                    "role"
                ),
                "start": item.get(
                    "start"
                ),
                "end": item.get(
                    "end"
                ),
                "achievements": item.get(
                    "achievements",
                    [],
                ),
            }
        )

    projects = []

    for item in profile.get(
        "projects",
        [],
    ):
        projects.append(
            {
                "name": item.get(
                    "name"
                ),
                "technologies": item.get(
                    "technologies",
                    [],
                ),
            }
        )

    education = []

    for item in profile.get(
        "education",
        [],
    ):
        education.append(
            {
                "degree": item.get(
                    "degree"
                ),
                "institution": item.get(
                    "institution"
                ),
                "start": item.get(
                    "start"
                ),
                "end": item.get(
                    "end"
                ),
            }
        )

    return {
        "candidate_name": profile.get(
            "name"
        ),
        "professional_experience": experience,
        "personal_projects": projects,
        "skills": profile.get(
            "skills",
            [],
        ),
        "education": education,
        "summary": profile.get(
            "summary",
            "",
        ),
    }

def select_relevant_candidate_evidence(
    profile: dict,
    job: dict,
) -> dict:
    """
    Select candidate facts that are genuinely relevant to the job.

    This keeps the language model from freely combining unrelated
    employers, projects, and technologies.
    """

    job_text = normalize_for_matching(
        str(job.get("description", ""))
    )

    selected_experience = []
    selected_projects = []

    # Technologies/terms that are safe to match directly against
    # the job posting.
    relevant_terms = [
        "react",
        "next.js",
        "nextjs",
        "javascript",
        "typescript",
        "frontend",
        "front-end",
        "responsive",
        "ui",
        "api",
        "rest",
        "firebase",
        "redux",
        "tailwind",
        "html",
        "css",
        "performance",
        "routing",
        "components",
        "state management",
        "web development",
    ]

    matched_terms = [
        term
        for term in relevant_terms
        if term in job_text
    ]

    # Keep the complete professional experience records.
    # We do NOT let the model merge individual achievements
    # across employers.
    for item in profile.get(
        "experience",
        [],
    ):
        selected_experience.append(
            {
                "company": item.get("company"),
                "role": item.get("role"),
                "start": item.get("start"),
                "end": item.get("end"),
                "achievements": list(
                    item.get(
                        "achievements",
                        [],
                    )
                ),
            }
        )

    # Select only projects whose technologies overlap with
    # the job's actual terminology.
    for item in profile.get(
        "projects",
        [],
    ):
        technologies = item.get(
            "technologies",
            [],
        )

        matching_technologies = [
            technology
            for technology in technologies
            if normalize_for_matching(
                str(technology)
            ) in job_text
        ]

        if matching_technologies:
            selected_projects.append(
                {
                    "name": item.get("name"),
                    "technologies": matching_technologies,
                }
            )

    return {
        "candidate_name": profile.get(
            "name"
        ),
        "target_role": job.get(
            "title"
        ),
        "matched_job_terms": matched_terms,
        "professional_experience": selected_experience,
        "relevant_personal_projects": selected_projects,
        "skills": profile.get(
            "skills",
            [],
        ),
        "education": profile.get(
            "education",
            [],
        ),
    }

def build_cover_letter_prompt(
    profile: dict,
    job: dict,
) -> str:
    company = str(
        job.get(
            "company",
            "the company",
        )
    ).strip()

    title = str(
        job.get(
            "title",
            "the position",
        )
    ).strip()

    location = str(
        job.get(
            "location",
            "",
        )
    ).strip()

    description = str(
        job.get(
            "description",
            "",
        )
    ).strip()

    if not description:
        raise ValueError(
            "The selected job has no job description."
        )

    candidate_evidence = select_relevant_candidate_evidence(
        profile,
        job,
    )

    evidence_json = json.dumps(
        candidate_evidence,
        indent=2,
        ensure_ascii=False,
    )

    return f"""
Write a professional cover letter for this specific job.

TARGET:
Company: {company}
Role: {title}
Location: {location}

CANDIDATE EVIDENCE:
{evidence_json}

JOB POSTING:
{description}

STRICT FACTUAL RULES:

1. The candidate evidence is the only source of truth.

2. Use only facts explicitly present in the candidate evidence.

3. Professional experience records are separate.
   Never move an achievement, responsibility, technology,
   or project from one employer to another.

4. Personal projects are separate from employment.
   Never describe a personal project as work performed
   for an employer.

5. Do not combine technologies from different employers
   into one employer's experience.

6. Do not assign a project technology to an employer.

7. Do not invent outcomes such as:
   improved user experience,
   increased performance,
   increased scalability,
   improved maintainability,
   seamless experience,
   high performance,
   major impact,
   significant impact,
   or measurable results.

8. Do not use words such as:
   cutting-edge,
   innovative,
   passionate,
   perfect fit,
   ideal candidate,
   seasoned,
   expert,
   highly experienced,
   world-class,
   industry-leading,
   exceptional,
   outstanding.

9. Do not describe the candidate's education as current unless
   the candidate evidence explicitly says it is current.

10. Do not make claims about Eudia, its mission, products,
    culture, technology, or industry unless those claims are
    directly supported by the job posting.

11. Do not claim legal, AI, enterprise, or other domain
    experience unless it is explicitly present in the
    candidate evidence.

12. Do not say that a project "allowed", "enabled", "prepared",
    "equipped", "positioned", "honed", or "demonstrated"
    an ability unless the underlying factual statement is
    explicitly present in the evidence.

13. Prefer simple factual statements:
    "I developed..."
    "I implemented..."
    "I integrated..."
    "I built..."
    "I used..."

14. Do not infer a result from an activity.

15. Do not infer a responsibility from a technology.

16. Do not infer an employer/project relationship.

17. The job posting determines relevance, but it does NOT
    give you permission to invent candidate experience.

WRITING:

- Write exactly 4 paragraphs.
- Target approximately 220-280 words.
- Paragraph 1: direct application + 1-2 concrete relevant facts.
- Paragraph 2: professional experience with concrete facts.
- Paragraph 3: one relevant personal project OR additional
  professional experience.
- Paragraph 4: concise closing connecting the documented
  experience to the role without making unsupported claims.
- Use factual, restrained language.
- Do not summarize the entire resume.
- Do not repeat the same fact.
- Do not praise the company without evidence.

OPENING:

Start directly with:

Dear Hiring Team,

Do not use:
"I am writing to express my enthusiastic interest..."
"I am excited to apply..."
"I am thrilled to apply..."
"I believe I am the perfect fit..."
"I am confident that I am an ideal candidate..."

FORMAT:

Return ONLY the cover-letter body.

Do not include:
- address
- date
- phone number
- email
- LinkedIn
- GitHub
- portfolio URL
- Subject line
- Markdown
- bullet points
- headings
- placeholders
- commentary
- analysis

End exactly with:

Best regards,
MD SAFI MAAZ
""".strip()

def revise_cover_letter(
    cover_letter: str,
    validation_error: str,
    profile: dict,
    job: dict,
) -> str:
    """
    Ask the local model to revise a rejected cover letter.

    The revision is based on the original candidate evidence and
    the deterministic validation error. The model must not invent
    new candidate facts while correcting the draft.
    """

    candidate_evidence = build_candidate_evidence(
        profile
    )

    evidence_json = json.dumps(
        candidate_evidence,
        indent=2,
        ensure_ascii=False,
    )

    company = str(
        job.get(
            "company",
            "",
        )
    ).strip()

    title = str(
        job.get(
            "title",
            "",
        )
    ).strip()

    revision_prompt = f"""
Revise the cover letter below.

TARGET:
Company: {company}
Role: {title}

CANDIDATE EVIDENCE:
{evidence_json}

ORIGINAL COVER LETTER:
{cover_letter}

VALIDATION ERROR:
{validation_error}

You MUST fix the validation error.

You MUST also follow all of these rules:

1. Candidate evidence is the only source of truth.

2. Never invent an employer, project, responsibility,
   achievement, metric, qualification, technology, client,
   domain experience, or company fact.

3. Professional experience and personal projects are separate.
   Never say that a personal project was created at an employer.

4. Never move a technology or responsibility from one
   employer/project to another.

5. Do not claim current education or current employment unless
   the evidence explicitly says it is current.

6. Do not invent results or performance improvements.

7. Do not make claims about Eudia unless directly supported
   by the job posting.

8. Do not use:
   passionate
   detail-oriented
   cutting-edge
   innovative
   perfect fit
   ideal candidate
   seasoned
   expert
   highly experienced
   excited to apply
   excited to join
   thrilled
   world-class
   industry-leading

9. Do not use vague claims such as:
   "honed my ability"
   "showcased my ability"
   "demonstrated my ability"
   "made a significant impact"
   "proven track record"
   "deliver exceptional results"

10. Keep concrete facts from the candidate evidence.

11. Write exactly 4 short paragraphs.

12. Target approximately 220-280 words.

13. Start exactly with:

Dear Hiring Team,

14. Return ONLY the cover-letter body.

15. Do not include:
   address
   date
   phone
   email
   links
   subject
   headings
   bullet points
   Markdown
   commentary
   analysis
   placeholders

16. End exactly with:

Best regards,
MD SAFI MAAZ
""".strip()

    response = ask_cover_letter_ai(
        revision_prompt
    )

    return clean_cover_letter(
        response
    )

def generate_cover_letter(
    job: dict,
) -> str:
    profile = load_profile()

    prompt = build_cover_letter_prompt(
        profile,
        job,
    )

    print()
    print("=" * 80)
    print("GENERATING COVER LETTER")
    print("=" * 80)
    print()

    print(
        f"Company: {job.get('company', 'Unknown')}"
    )

    print(
        f"Role: {job.get('title', 'Unknown')}"
    )

    print()

    print(
        f"Using local Ollama model: "
        f"{COVER_LETTER_MODEL}"
    )

    print(
        "Generating a fresh job-specific cover letter..."
    )

    print()

    raw_response = ask_cover_letter_ai(
        prompt
    )

    cover_letter = clean_cover_letter(
        raw_response
    )

    max_attempts = 3

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        print()
        print("=" * 80)
        print(
            f"DRAFT VALIDATION "
            f"(attempt {attempt}/{max_attempts})"
        )
        print("=" * 80)
        print()

        print(cover_letter)
        print()

        try:
            validate_cover_letter(
                cover_letter,
                profile,
                job,
            )

            print(
                "VALIDATION PASSED"
            )

            return cover_letter

        except ValueError as error:
            validation_error = str(error)

            print(
                "VALIDATION FAILED:"
            )
            print(
                validation_error
            )

            if attempt >= max_attempts:
                raise ValueError(
                    "Cover letter failed validation after "
                    f"{max_attempts} attempts. "
                    f"Last error: {validation_error}"
                )

            print()
            print(
                "Asking the local model to correct "
                "the rejected draft..."
            )

            cover_letter = revise_cover_letter(
                cover_letter,
                validation_error,
                profile,
                job,
            )

    raise RuntimeError(
        "Unexpected cover-letter generation state."
    )

def save_cover_letter(
    job_id: int,
    cover_letter: str,
) -> Path:
    COVER_LETTERS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        COVER_LETTERS_DIR
        / f"job_{job_id}.txt"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        file.write(
            cover_letter.strip()
            + "\n"
        )

    return output_file


def get_job(job_id: int):
    connection = get_connection()

    try:
        job = connection.execute(
            """
            SELECT
                id,
                company,
                title,
                location,
                url,
                description,
                match_score,
                recommendation
            FROM jobs
            WHERE id = ?
            """,
            (job_id,),
        ).fetchone()

    finally:
        connection.close()

    return job


def generate_cover_letter_for_job(
    job_id: int,
) -> Path:
    job_row = get_job(job_id)

    if job_row is None:
        raise ValueError(
            f"Job {job_id} was not found in the database."
        )

    job = dict(job_row)

    cover_letter = generate_cover_letter(
        job
    )

    output_file = save_cover_letter(
        job_id,
        cover_letter,
    )

    print(
        f"Cover letter saved to: {output_file}"
    )

    return output_file


def main():
    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: "
            "python -m app.application.cover_letter <job_id>"
        )
        raise SystemExit(1)

    try:
        job_id = int(sys.argv[1])
    except ValueError:
        print("Job ID must be an integer.")
        raise SystemExit(1)

    output_file = generate_cover_letter_for_job(
        job_id
    )

    print()
    print("=" * 80)
    print("COVER LETTER GENERATED SUCCESSFULLY")
    print("=" * 80)
    print()
    print(f"File: {output_file}")
    print()


if __name__ == "__main__":
    main()