import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
ANSWERS_PATH = BASE_DIR / "data" / "answers.json"


def normalize_question(question: str) -> str:
    """
    Normalize a question so small wording differences
    do not create duplicate answers.
    """
    return " ".join(question.lower().strip().split())


def load_answers() -> dict:
    """
    Load reusable answers from data/answers.json.
    """
    if not ANSWERS_PATH.exists():
        return {}

    try:
        with ANSWERS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return {}

        return data

    except (json.JSONDecodeError, OSError):
        return {}


def save_answers(answers: dict) -> None:
    """
    Save reusable answers to data/answers.json.
    """
    ANSWERS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with ANSWERS_PATH.open("w", encoding="utf-8") as f:
        json.dump(answers, f, indent=2, ensure_ascii=False)


def get_answer(question: str) -> str | None:
    """
    Return a previously saved answer for a question.

    Returns None when no answer exists.
    """
    normalized = normalize_question(question)

    if not normalized:
        return None

    answers = load_answers()

    return answers.get(normalized)


def has_answer(question: str) -> bool:
    """
    Check whether a reusable answer exists.
    """
    return get_answer(question) is not None


def save_answer(question: str, answer: str) -> None:
    """
    Save a reusable answer for a question.
    """
    normalized_question = normalize_question(question)

    if not normalized_question:
        return

    answers = load_answers()
    answers[normalized_question] = answer.strip()

    save_answers(answers)


if __name__ == "__main__":
    print(f"Answer store: {ANSWERS_PATH}")