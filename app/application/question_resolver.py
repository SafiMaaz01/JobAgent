from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re

from app.application.answers import get_answer


BASE_DIR = Path(__file__).resolve().parents[2]
PROFILE_PATH = BASE_DIR / "data" / "profile.json"


@dataclass
class QuestionResolution:
    question: str
    status: str
    answer: str | None = None
    source: str | None = None
    reason: str | None = None


def normalize_question(question: str) -> str:
    question = question.lower().strip()
    question = re.sub(r"\s+", " ", question)
    question = re.sub(r"[?*]+$", "", question)
    return question.strip()


def load_profile() -> dict:
    if not PROFILE_PATH.exists():
        return {}

    try:
        with PROFILE_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return {}

        return data

    except (json.JSONDecodeError, OSError):
        return {}


def is_legal_or_authorization_question(question: str) -> bool:
    text = normalize_question(question)

    patterns = [
        r"\bvisa\b",
        r"sponsorship",
        r"work authorization",
        r"authorized to work",
        r"legally authorized",
        r"legally eligible",
        r"right to work",
        r"immigration",
        r"employment authorization",
        r"require.*sponsor",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def is_salary_question(question: str) -> bool:
    text = normalize_question(question)

    patterns = [
        r"\bsalary\b",
        r"compensation",
        r"expected pay",
        r"expected compensation",
        r"desired pay",
        r"salary expectation",
        r"pay expectation",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def is_relocation_question(question: str) -> bool:
    text = normalize_question(question)

    patterns = [
        r"willing to relocate",
        r"willing.*relocation",
        r"open to relocation",
        r"\brelocate\b",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def is_react_experience_question(question: str) -> bool:
    text = normalize_question(question)

    return bool(
        re.search(r"\breact(?:\.js|js)?\b", text)
        and re.search(
            r"experience|worked|work with|proficien|familiar|know|used",
            text,
        )
    )


def is_nextjs_experience_question(question: str) -> bool:
    text = normalize_question(question)

    return bool(
        re.search(r"\bnext(?:\.js|js)\b", text)
        and re.search(
            r"experience|worked|work with|proficien|familiar|know|used",
            text,
        )
    )


def is_typescript_experience_question(question: str) -> bool:
    text = normalize_question(question)

    return bool(
        re.search(r"\btypescript\b", text)
        and re.search(
            r"experience|worked|work with|proficien|familiar|know|used",
            text,
        )
    )


def is_location_question(question: str) -> bool:
    text = normalize_question(question)

    patterns = [
        r"where are you currently located",
        r"current location",
        r"where do you live",
        r"\blocation\b",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def answer_from_profile(question: str, profile: dict) -> str | None:
    if is_legal_or_authorization_question(question):
        return None

    if is_salary_question(question):
        return None

    if is_relocation_question(question):
        preferences = profile.get("application_preferences", {})

        if preferences.get("willing_to_relocate") is True:
            return "Yes"

        if preferences.get("willing_to_relocate") is False:
            return "No"

        return None

    if is_react_experience_question(question):
        skills = {
            str(skill).lower()
            for skill in profile.get("skills", [])
        }

        if "react.js" in skills or "react" in skills:
            return (
                "Yes, I have professional experience building web "
                "applications with React and Next.js."
            )

        return None

    if is_nextjs_experience_question(question):
        skills = {
            str(skill).lower()
            for skill in profile.get("skills", [])
        }

        if "next.js" in skills or "nextjs" in skills:
            return (
                "Yes, I have professional experience building web "
                "applications with Next.js and React."
            )

        return None

    if is_typescript_experience_question(question):
        skills = {
            str(skill).lower()
            for skill in profile.get("skills", [])
        }

        if "typescript" in skills:
            return (
                "Yes, I have hands-on experience using TypeScript "
                "in web applications."
            )

        return None

    if is_location_question(question):
        location = profile.get("location")

        if isinstance(location, str) and location.strip():
            return location.strip()

        return None

    return None


def resolve_question(question: str) -> QuestionResolution:
    question = question.strip()

    if not question:
        return QuestionResolution(
            question=question,
            status="ASK_USER",
            reason="The application question is empty.",
        )

    saved_answer = get_answer(question)

    if saved_answer is not None:
        return QuestionResolution(
            question=question,
            status="ANSWER",
            answer=saved_answer,
            source="answers.json",
            reason="A previously approved answer exists.",
        )

    if is_legal_or_authorization_question(question):
        return QuestionResolution(
            question=question,
            status="ASK_USER",
            reason=(
                "Legal or work-authorization questions must be "
                "answered explicitly by the user."
            ),
        )

    if is_salary_question(question):
        return QuestionResolution(
            question=question,
            status="ASK_USER",
            reason=(
                "Salary expectations are not automatically inferred "
                "from the minimum salary preference."
            ),
        )

    profile = load_profile()

    profile_answer = answer_from_profile(
        question,
        profile,
    )

    if profile_answer is not None:
        return QuestionResolution(
            question=question,
            status="ANSWER",
            answer=profile_answer,
            source="profile.json",
            reason=(
                "The answer is directly supported by the "
                "candidate profile."
            ),
        )

    return QuestionResolution(
        question=question,
        status="ASK_USER",
        reason=(
            "No saved answer exists and the profile does not provide "
            "enough explicit information to answer safely."
        ),
    )


def main() -> None:
    test_questions = [
        "Do you have experience with React?",
        "Are you willing to relocate?",
        "Do you require visa sponsorship?",
        "What is your expected salary?",
        "Where are you currently located?",
        "Have you worked with Next.js?",
        "How many years of Python experience do you have?",
    ]

    print("=" * 80)
    print("JOBAGENT QUESTION RESOLVER TEST")
    print("=" * 80)

    for question in test_questions:
        result = resolve_question(question)

        print()
        print(f"Question: {result.question}")
        print(f"Status:   {result.status}")
        print(f"Answer:   {result.answer}")
        print(f"Source:   {result.source}")
        print(f"Reason:   {result.reason}")

    print()
    print("=" * 80)
    print("RESOLVER TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()