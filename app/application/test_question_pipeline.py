from app.application.question_resolver import resolve_question


def run_test(question: str, expected_status: str, expected_source: str | None = None):
    result = resolve_question(question)

    print(f"Question: {question}")
    print(f"  Status:  {result.status}")
    print(f"  Source:  {result.source}")
    print(f"  Answer:  {result.answer}")
    print(f"  Reason:  {result.reason}")

    assert result.status == expected_status, (
        f"Expected status {expected_status!r}, got {result.status!r}"
    )

    if expected_source is not None:
        assert result.source == expected_source, (
            f"Expected source {expected_source!r}, got {result.source!r}"
        )

    if expected_status == "ANSWER":
        assert result.answer, "ANSWER result must contain an answer."

    print("  PASS\n")


def main():
    print("=" * 80)
    print("JOBAGENT APPLICATION QUESTION PIPELINE TEST")
    print("=" * 80)
    print()

    # 1. Saved reusable answer from data/answers.json
    run_test(
        "Do you have experience with React?",
        "ANSWER",
        "answers.json",
    )

    # 2. Saved reusable answer for relocation
    run_test(
        "Are you willing to relocate?",
        "ANSWER",
        "answers.json",
    )

    # 3. Profile-derived answer
    run_test(
        "Have you worked with Next.js?",
        "ANSWER",
        "profile.json",
    )

    # 4. Profile-derived current location
    run_test(
        "Where are you currently located?",
        "ANSWER",
        "profile.json",
    )

    # 5. Legal/work authorization questions must never be guessed.
    run_test(
        "Do you require visa sponsorship?",
        "ASK_USER",
    )

    # 6. Salary questions must be explicitly provided by the user.
    run_test(
        "What is your expected salary?",
        "ASK_USER",
    )

    # 7. Unsupported experience must not be invented.
    run_test(
        "How many years of Python experience do you have?",
        "ASK_USER",
    )

    print("=" * 80)
    print("ALL PIPELINE TESTS PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()
