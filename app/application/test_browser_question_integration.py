import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from app.browser.autofill_application import process_application_questions
from app.application.answers import load_answers, save_answers


BASE_DIR = Path(__file__).resolve().parents[2]
ANSWERS_PATH = BASE_DIR / "data" / "answers.json"

TEST_QUESTION = "JobAgent integration test question - what is your preferred test value?"
TEST_ANSWER = "JobAgent test answer"


def main():
    original_answers = load_answers()

    html = f"""
    <!doctype html>
    <html>
    <body>
        <form>
            <label for="test_question">{TEST_QUESTION}</label>
            <input id="test_question" type="text" required>
        </form>
    </body>
    </html>
    """

    print("=" * 80)
    print("JOBAGENT BROWSER QUESTION INTEGRATION TEST")
    print("=" * 80)
    print()
    print("A local test page will be opened.")
    print("It does not connect to any job site.")
    print()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            page.set_content(html)

            results = process_application_questions(
                page,
                {},
                handled_question_ids=set(),
            )

            # The interactive handler is expected to receive the answer
            # from the terminal. The result must show it was asked and filled.
            asked = results["asked_questions"]
            filled = results["filled_answers"]

            assert len(asked) == 1, f"Expected 1 asked question, got {len(asked)}"
            assert asked[0]["question"] == TEST_QUESTION
            assert asked[0]["answer"] == TEST_ANSWER

            assert len(filled) == 1, f"Expected 1 filled answer, got {len(filled)}"
            assert page.locator("#test_question").input_value() == TEST_ANSWER

            saved_answers = load_answers()
            assert (
                saved_answers.get(TEST_QUESTION.lower())
                == TEST_ANSWER
            ), "Answer was not saved to answers.json"

            print()
            print("=" * 80)
            print("INTEGRATION TEST PASSED")
            print("=" * 80)
            print()
            print("Verified:")
            print("- Real Playwright text control was detected")
            print("- Resolver found no safe automatic answer")
            print("- JobAgent asked the user")
            print("- User answer was saved to answers.json")
            print("- Answer was filled into the browser control")
            print()

            browser.close()

    finally:
        # Restore the user's real answer database exactly as it was before
        # this test. The temporary test answer must never remain.
        save_answers(original_answers)


if __name__ == "__main__":
    main()
