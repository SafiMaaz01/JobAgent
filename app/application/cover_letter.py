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

COVER_LETTER_MODEL = "gpt-oss:latest"

OLLAMA_URL = "http://localhost:11434/api/generate"


def load_profile():
    with PROFILE_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def ask_cover_letter_ai(prompt: str) -> str:
    """
    Generate a cover letter using the dedicated local
    GPT-OSS model.

    Job matching remains completely separate and continues
    using qwen2.5:7b.
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": COVER_LETTER_MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.55,
                "top_p": 0.9,
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
        "The cover-letter model returned no final response. "
        f"Ollama response keys: {list(data.keys())}"
    )


def clean_cover_letter(text: str) -> str:
    if not text:
        return ""

    text = text.strip()

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

    text = re.sub(
        r"^subject\s*:\s*.*\n+",
        "",
        text,
        flags=re.IGNORECASE,
    )

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

    if (
        len(text) >= 2
        and text.startswith('"')
        and text.endswith('"')
    ):
        text = text[1:-1].strip()

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def validate_cover_letter(
    cover_letter: str,
    profile: dict,
    job: dict,
) -> None:
    """
    Conservative validation.

    This catches obvious model failures. The generation prompt
    remains responsible for factual grounding.
    """

    if not cover_letter:
        raise ValueError(
            "The AI returned an empty cover letter."
        )

    if len(cover_letter) < 300:
        raise ValueError(
            "The generated cover letter is unexpectedly short."
        )

    if len(cover_letter) > 5000:
        raise ValueError(
            "The generated cover letter is unexpectedly long."
        )

    forbidden_patterns = [
        r"\[insert",
        r"\[your ",
        r"<your ",
        r"\bplaceholder\b",
        r"\bcompany name\b",
        r"\bjob title\b",
        r"\byour company\b",
        r"\[company\]",
        r"\[role\]",
        r"\[position\]",
        r"\[candidate\]",
        r"\[name\]",
    ]

    for pattern in forbidden_patterns:
        if re.search(
            pattern,
            cover_letter,
            flags=re.IGNORECASE,
        ):
            raise ValueError(
                "The generated cover letter contains "
                "an unresolved placeholder."
            )

    forbidden_meta_patterns = [
        r"^here is",
        r"^here's",
        r"^sure[,!]",
        r"^certainly[,!]",
        r"^of course[,!]",
        r"^cover letter:",
        r"^final answer:",
    ]

    for pattern in forbidden_meta_patterns:
        if re.search(
            pattern,
            cover_letter,
            flags=re.IGNORECASE,
        ):
            raise ValueError(
                "The generated cover letter contains "
                "model meta-commentary."
            )

    name = str(
        profile.get(
            "name",
            "",
        )
    ).strip()

    if name:
        name_parts = [
            part
            for part in name.split()
            if len(part) >= 2
        ]

        if name_parts and not any(
            part.lower() in cover_letter.lower()
            for part in name_parts
        ):
            raise ValueError(
                "The generated cover letter does not "
                "appear to reference the candidate."
            )

    company = str(
        job.get(
            "company",
            "",
        )
    ).strip()

    if company and company.lower() not in cover_letter.lower():
        raise ValueError(
            "The generated cover letter does not "
            "reference the target company."
        )

    title = str(
        job.get(
            "title",
            "",
        )
    ).strip()

    if title:
        title_words = [
            word
            for word in re.findall(
                r"[A-Za-z0-9]+",
                title,
            )
            if len(word) >= 3
        ]

        if title_words:
            matching_words = sum(
                1
                for word in title_words
                if word.lower()
                in cover_letter.lower()
            )

            if matching_words == 0:
                raise ValueError(
                    "The generated cover letter does not "
                    "appear to reference the target role."
                )


def build_candidate_evidence(profile: dict) -> dict:
    """
    Preserve strict evidence boundaries.

    The model must not assume that a skill, technology,
    responsibility, or achievement listed in one section
    belongs to another section.
    """

    return {
        "personal": {
            "name": profile.get("name"),
            "location": profile.get("location"),
        },
        "overall_skills": profile.get(
            "skills",
            [],
        ),
        "summary": profile.get(
            "summary",
            "",
        ),
        "professional_experience": profile.get(
            "experience",
            [],
        ),
        "education": profile.get(
            "education",
            [],
        ),
        "projects": profile.get(
            "projects",
            [],
        ),
        "target_roles": profile.get(
            "target_roles",
            [],
        ),
    }


def build_cover_letter_prompt(
    profile: dict,
    job: dict,
) -> str:
    company = job.get(
        "company",
        "the company",
    )

    title = job.get(
        "title",
        "the position",
    )

    location = job.get(
        "location",
        "",
    )

    description = job.get(
        "description",
        "",
    )

    if not description:
        raise ValueError(
            "The selected job has no job description."
        )

    candidate_evidence = build_candidate_evidence(
        profile
    )

    return f"""
You are an expert professional career writer.

Write ONE polished, concise, natural, job-specific cover
letter for the candidate.

The final letter will be reviewed by a real recruiter.

Accuracy is more important than sounding impressive.

============================================================
TARGET JOB
============================================================

Company:
{company}

Role:
{title}

Location:
{location}

============================================================
CANDIDATE EVIDENCE
============================================================

Everything below is factual candidate information.

Different sections represent different evidence boundaries.

Do NOT merge facts between employers or projects.

{json.dumps(
    candidate_evidence,
    indent=2,
    ensure_ascii=False,
)}

============================================================
FULL JOB POSTING
============================================================

{description}

============================================================
ABSOLUTE FACTUAL RULE
============================================================

You MUST NOT invent anything.

The candidate evidence above is the complete source of truth.

If a fact is not present in the candidate evidence,
you cannot use that fact.

If a project is not listed in the candidate evidence,
you MUST NOT mention that project.

Never invent a project.

Never invent a responsibility.

Never invent an achievement.

Never invent a technology.

Never invent a client.

Never invent a metric.

Never invent a qualification.

Never invent years of experience.

Never invent domain experience.

============================================================
EMPLOYER EVIDENCE BOUNDARIES
============================================================

Each professional experience entry is independent.

If IT FOSTERS contains React and Next.js, those technologies
may be associated with IT FOSTERS.

If Sparrow Softtech does not explicitly list React or Next.js,
do NOT associate those technologies with Sparrow Softtech.

Never transfer technologies or responsibilities from one
employer to another.

============================================================
PROJECT EVIDENCE BOUNDARIES
============================================================

Each project is independent.

For example, if Draftly contains:

Next.js 16
Convex
Better Auth
Tailwind CSS v4
shadcn/ui
TipTap

those are the technologies you may associate with Draftly.

Do not add Redux Toolkit, Firebase, Sanity, Framer Motion,
Clerk, or other technologies to Draftly unless they are
explicitly listed under Draftly.

Never invent project features or outcomes.

============================================================
OVERALL SKILLS RULE
============================================================

The overall_skills list represents skills the candidate has.

However, a skill listed only in overall_skills does not prove
where or how the candidate used that skill.

Therefore, do not attach an overall skill to a particular
employer or project unless that employer/project explicitly
supports the claim.

============================================================
JOB REQUIREMENT RULE
============================================================

Read the entire job posting before writing.

Identify the most important:

- responsibilities
- technical requirements
- frameworks
- frontend requirements
- experience requirements
- collaboration expectations
- qualifications

Then select only candidate evidence that genuinely connects
to those requirements.

If a job requirement is not supported by the candidate,
do not pretend it is supported.

============================================================
EXPERIENCE LEVEL
============================================================

The candidate has approximately one year of professional
experience according to the profile.

Do not describe the candidate as:

seasoned
senior
highly experienced
extensively experienced

unless the supplied evidence explicitly supports it.

Prefer:

hands-on experience
professional experience
experience building
experience developing

============================================================
COMPANY CLAIMS
============================================================

Use the job posting as the only source for statements about
the company.

Do not invent company facts.

Do not call the company:

innovative
cutting-edge
industry-leading
revolutionary
fast-growing

or similar unless the job posting explicitly supports it
and the statement is genuinely useful.

Do not flatter the company.

============================================================
DOMAIN EXPERIENCE
============================================================

If the company operates in a specialized domain, do not claim
the candidate has experience in that domain unless the
candidate evidence explicitly supports it.

Focus instead on genuine transferable technical experience.

============================================================
WRITING STYLE
============================================================

Write like an excellent human applicant.

The writing should be:

professional
specific
clear
confident
natural
concise
credible

Avoid:

generic AI language
resume dumping
buzzwords
exaggeration
empty enthusiasm
company flattery
repetition

Do not write like a marketing brochure.

============================================================
OPENING
============================================================

Do NOT begin with:

"I am writing to express my enthusiastic interest..."

"I am excited to apply..."

"I am thrilled to apply..."

"I believe I am the perfect fit..."

"I am confident that I am an ideal candidate..."

Instead, begin directly with a specific connection between
the candidate's actual experience and this particular role.

============================================================
PROFESSIONAL EXPERIENCE
============================================================

Use professional experience when relevant.

Prefer concrete responsibilities.

For each employer mentioned, use only facts explicitly
associated with that employer.

============================================================
PROJECTS
============================================================

Mention a project only if it genuinely strengthens the
application.

Only mention projects that actually exist in the candidate
evidence.

When mentioning a project:

Use only its explicitly listed technologies and facts.

Do not invent project features.

Do not invent project outcomes.

Do not invent users.

Do not invent metrics.

============================================================
STRUCTURE
============================================================

Use approximately four short paragraphs.

Paragraph 1:
Immediately establish the strongest factual connection
between the candidate and this specific role.

Paragraph 2:
Explain the most relevant professional experience.

Paragraph 3:
Use one relevant project or additional technical evidence
only if it genuinely strengthens the application.

Paragraph 4:
Close professionally and concisely.

============================================================
LENGTH
============================================================

Target approximately 250-350 words.

Do not pad the letter.

Do not repeat the same skill multiple times.

A concise truthful letter is better than a longer generic one.

============================================================
FORMAT
============================================================

Return plain text only.

No Markdown.

No bullet points.

No headings.

No Subject line.

No analysis.

No explanation.

No preamble.

Start directly with:

Dear Hiring Team,

End exactly with:

Best regards,
MD SAFI MAAZ

Do not include:

phone number
email
LinkedIn
GitHub
portfolio URL
physical address

Those are handled separately by the application system.

============================================================
FINAL FACT CHECK
============================================================

Before returning the letter, silently check every factual
statement.

For every employer:

Is this fact explicitly associated with that employer?

For every project:

Is this project actually listed?

Is this technology actually listed for that project?

For every technology:

Is the claim supported?

For every achievement:

Is it explicitly supported?

For every company statement:

Is it supported by the job posting?

For every experience-level statement:

Is it supported by the candidate evidence?

If any statement is unsupported, remove it.

Do not replace unsupported information with an invented fact.

============================================================
FINAL OUTPUT
============================================================

Return ONLY the finished cover letter.

No commentary.

No analysis.

No explanation.

No alternatives.

No notes.
"""


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
        "Thinking disabled for focused writing."
    )
    print(
        "Generating a fresh job-specific "
        "cover letter..."
    )
    print()

    raw_response = ask_cover_letter_ai(
        prompt
    )

    cover_letter = clean_cover_letter(
        raw_response
    )

    validate_cover_letter(
        cover_letter,
        profile,
        job,
    )

    return cover_letter


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