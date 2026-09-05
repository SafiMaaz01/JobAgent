from playwright.sync_api import sync_playwright


APPLICATION_URL = (
    "https://job-boards.greenhouse.io/"
    "eudia/jobs/4163890009"
)


def main():
    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        print("=" * 80)
        print("OPENING APPLICATION PAGE")
        print("=" * 80)

        page.goto(
            APPLICATION_URL,
            wait_until="domcontentloaded",
        )

        page.wait_for_timeout(3000)

        print()
        print("=" * 80)
        print("EXACT QUESTION LABELS")
        print("=" * 80)

        question_ids = [
            "question_5428820009",
            "question_5428822009",
        ]

        for question_id in question_ids:

            print()
            print("-" * 80)
            print(f"FIELD: {question_id}")
            print("-" * 80)

            field = page.locator(
                f"#{question_id}"
            )

            print(
                "Field exists:",
                field.count() > 0,
            )

            if field.count() == 0:
                continue

            labelled_by = field.get_attribute(
                "aria-labelledby"
            )

            print(
                "aria-labelledby:",
                labelled_by,
            )

            described_by = field.get_attribute(
                "aria-describedby"
            )

            print(
                "aria-describedby:",
                described_by,
            )

            if labelled_by:

                ids = labelled_by.split()

                for label_id in ids:

                    label = page.locator(
                        f"#{label_id}"
                    )

                    if label.count():

                        print(
                            f"Label [{label_id}]:"
                        )

                        print(
                            label.inner_text()
                            .strip()
                        )

                        print()
                        print(
                            "Label HTML:"
                        )

                        print(
                            label.evaluate(
                                "(el) => el.outerHTML"
                            )
                        )

            # Find the nearest form-field container.
            container = field.locator(
                "xpath=ancestor::*["
                "contains(@class, 'field')"
                "][1]"
            )

            if container.count():

                print()
                print(
                    "Nearest field container:"
                )

                print(
                    container.inner_text()
                    .strip()
                )

        print()
        print("=" * 80)
        print("NOTHING WAS SELECTED")
        print("NOTHING WAS FILLED")
        print("NOTHING WAS SUBMITTED")
        print("=" * 80)

        input(
            "\nPress Enter to close the browser..."
        )

        browser.close()


if __name__ == "__main__":
    main()