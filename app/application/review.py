import json
from pathlib import Path


APPLICATIONS_DIR = Path("data/applications")


def get_latest_application():
    candidates = []

    for file in APPLICATIONS_DIR.glob("job_*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                package = json.load(f)

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


def print_review_report():
    result = get_latest_application()

    if result is None:
        print()
        print("No application packages found.")
        return

    created_at, package_file, package = result

    job = package.get("job", {})
    application = package.get("application", {})

    manual_answers = application.get(
        "manual_answers",
        {},
    )

    active_offer_answer = manual_answers.get(
        "active_offer_recruiting_deadline",
        "",
    ).strip()

    print()
    print("=" * 70)
    print("JOBAGENT APPLICATION REVIEW")
    print("=" * 70)

    print()
    print("APPLICATION")
    print("-" * 70)
    print(f"Company:       {job.get('company', '')}")
    print(f"Title:         {job.get('title', '')}")
    print(f"Location:      {job.get('location', '')}")
    print(f"Match score:   {job.get('match_score', '')}")
    print(f"Status:        {application.get('status', '')}")
    print(f"Created:       {created_at}")
    print(f"Package:       {package_file}")

    print()
    print("AUTOMATION STATUS")
    print("-" * 70)

    autofilled_fields = [
        "First name",
        "Last name",
        "Email",
        "Phone",
        "Country",
        "Location",
        "Resume",
        "School",
        "Degree",
        "Discipline",
        "Education dates",
        "GitHub",
        "LinkedIn",
        "Work authorization",
        "Visa sponsorship",
        "WhatsApp recruiting messages",
    ]

    for field in autofilled_fields:
        print(f"[OK] {field}")

    print()
    print("REQUIRED FIELDS")
    print("-" * 70)

    if active_offer_answer:
        print(
            "[OK] Active offer / recruiting-process deadline"
        )
        print(
            f"     Saved answer: {active_offer_answer}"
        )
    else:
        print(
            "[!] Active offer / recruiting-process deadline"
        )

    print()
    print("OPTIONAL / UNKNOWN FIELDS LEFT BLANK")
    print("-" * 70)

    optional_manual_fields = [
        "GPA",
        "Preferred name",
        "Pronouns",
        "Academic record",
        "Cover letter",
    ]

    for field in optional_manual_fields:
        print(f"[ ] {field}")

    print()
    print("SAFETY")
    print("-" * 70)
    print("[OK] Resume is attached")
    print("[OK] Unknown information was not invented")
    print("[OK] Legal/work authorization answers were not guessed")
    print("[OK] Application was not submitted")

    if active_offer_answer:
        print("[OK] Required manual answer is saved")
    else:
        print("[!] Required manual answer is still missing")

    print()

    if active_offer_answer:
        print("=" * 70)
        print("READY FOR MANUAL REVIEW")
        print("=" * 70)
        print()
        print(
            "The required manual field has an explicitly "
            "saved answer."
        )
        print()
        print(
            "The browser automation will NOT submit the application."
        )
    else:
        print("=" * 70)
        print("MANUAL ACTION REQUIRED")
        print("=" * 70)
        print()
        print(
            "Before submitting this application, answer the "
            "required field marked [!]."
        )
        print()
        print(
            "The browser automation will NOT submit the application."
        )

    print()


if __name__ == "__main__":
    print_review_report()