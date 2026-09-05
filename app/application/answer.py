import json
from pathlib import Path


APPLICATIONS_DIR = Path("data/applications")


def get_latest_application():
    candidates = []

    for file in APPLICATIONS_DIR.glob("job_*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                package = json.load(f)

            status = package.get("application", {}).get("status")

            if status != "ready_for_review":
                continue

            created_at = (
                package
                .get("application", {})
                .get("created_at", "")
            )

            candidates.append((created_at, file, package))

        except (json.JSONDecodeError, OSError):
            continue

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return candidates[0]


def save_package(package_file, package):
    with open(package_file, "w", encoding="utf-8") as f:
        json.dump(
            package,
            f,
            indent=2,
            ensure_ascii=False,
        )


def answer_required_question():
    result = get_latest_application()

    if result is None:
        print()
        print("No ready-for-review application found.")
        return

    created_at, package_file, package = result

    job = package.get("job", {})
    application = package.setdefault("application", {})

    manual_answers = application.setdefault(
        "manual_answers",
        {},
    )

    print()
    print("=" * 70)
    print("JOBAGENT APPLICATION ANSWERS")
    print("=" * 70)

    print()
    print(f"Company:  {job.get('company', '')}")
    print(f"Title:    {job.get('title', '')}")
    print(f"Package:  {package_file}")

    print()
    print("REQUIRED QUESTION")
    print("-" * 70)

    question_key = "active_offer_recruiting_deadline"

    existing_answer = manual_answers.get(question_key)

    if existing_answer:
        print()
        print("An answer is already saved:")
        print(f"  {existing_answer}")

        print()
        change = input(
            "Do you want to replace it? [y/N]: "
        ).strip().lower()

        if change != "y":
            print()
            print("Existing answer kept.")
            return

    print()
    print(
        "Stripe requires an answer about whether you have an "
        "active offer or another recruiting-process deadline."
    )

    print()
    print(
        "Enter the answer exactly as you want it represented."
    )

    print(
        "If you are unsure, press Enter without typing anything."
    )

    print()

    answer = input(
        "Your answer: "
    ).strip()

    if not answer:
        print()
        print("No answer entered.")
        print("The field remains unanswered.")
        print("Nothing was saved.")
        return

    manual_answers[question_key] = answer

    application["manual_answers"] = manual_answers

    save_package(package_file, package)

    print()
    print("=" * 70)
    print("ANSWER SAVED")
    print("=" * 70)

    print()
    print(f"Question: {question_key}")
    print(f"Answer:   {answer}")

    print()
    print(f"Updated package: {package_file}")
    print()
    print("The answer has NOT been submitted to Stripe.")
    print("The browser has NOT been opened.")
    print("The application has NOT been submitted.")
    print()


if __name__ == "__main__":
    answer_required_question()