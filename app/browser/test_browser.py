import json
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright


def load_application_package(package_path):
    application_package = Path(package_path).resolve()

    if not application_package.exists():
        raise FileNotFoundError(
            f"Application package not found: {application_package}"
        )

    with open(application_package, "r", encoding="utf-8") as file:
        return json.load(file)


def get_selected_value(page, selector):
    field = page.locator(selector).first

    container = field.locator(
        "xpath=ancestor::div[contains(@class,'select__control')]"
    ).first

    selected = container.locator(
        ".select__single-value"
    ).first

    if selected.count() == 0:
        return ""

    try:
        return selected.inner_text().strip()
    except Exception:
        return ""


def find_visible_option(page, expected_text):
    options = page.locator('[role="option"]:visible')

    for index in range(options.count()):
        option = options.nth(index)

        try:
            text = option.inner_text().strip()

            if text == expected_text:
                return option

        except Exception:
            continue

    for index in range(options.count()):
        option = options.nth(index)

        try:
            text = option.inner_text().strip()

            if expected_text.lower() in text.lower():
                return option

        except Exception:
            continue

    return None


def select_react_option(
    page,
    selector,
    search_text,
    expected_text,
    label,
    retries=3,
):
    print(f"\nOpening {label}...")

    field = page.locator(selector).first

    for attempt in range(1, retries + 1):
        print(f"Attempt {attempt}/{retries}")

        try:
            field.click()
            page.wait_for_timeout(300)

            search_input = field.locator(
                "xpath=ancestor::div[contains(@class,'select__control')]"
            ).first.locator(
                "input.select__input"
            ).first

            if search_input.count() == 0:
                print(
                    f"WARNING: React-Select search input "
                    f"not found for {label}."
                )
                continue

            search_input.focus()
            page.wait_for_timeout(100)
            search_input.fill("")

            search_input.press_sequentially(
                search_text,
                delay=50,
            )

            page.wait_for_timeout(800)

            options = page.locator(
                '[role="option"]:visible'
            )

            print(
                f"Visible filtered options for {label}: "
                f"{options.count()}"
            )

            for index in range(options.count()):
                option = options.nth(index)

                try:
                    print(
                        f"  {index + 1}. "
                        f"{option.inner_text().strip()}"
                    )
                except Exception:
                    pass

            target = find_visible_option(
                page,
                expected_text,
            )

            if target is not None:
                target.click()
                page.wait_for_timeout(500)

                selected_text = get_selected_value(
                    page,
                    selector,
                )

                print(
                    f"Selected {label}: "
                    f"{selected_text}"
                )

                if selected_text == expected_text:
                    return True

                if (
                    selected_text
                    and expected_text.lower()
                    in selected_text.lower()
                ):
                    return True

            print(
                f"No directly clickable option found "
                f"for {label}. Trying keyboard..."
            )

            search_input.focus()
            search_input.press("ArrowDown")
            page.wait_for_timeout(150)

            active_id = search_input.get_attribute(
                "aria-activedescendant"
            )

            if active_id:
                active = page.locator(
                    f"#{active_id}"
                ).first

                if active.count() > 0:
                    try:
                        active_text = (
                            active.inner_text().strip()
                        )

                        print(
                            "Keyboard highlighted option: "
                            f"{active_text}"
                        )

                        if (
                            active_text == expected_text
                            or expected_text.lower()
                            in active_text.lower()
                        ):
                            search_input.press("Enter")
                            page.wait_for_timeout(500)

                            selected_text = (
                                get_selected_value(
                                    page,
                                    selector,
                                )
                            )

                            print(
                                f"Keyboard selected {label}: "
                                f"{selected_text}"
                            )

                            if (
                                selected_text == expected_text
                                or (
                                    selected_text
                                    and expected_text.lower()
                                    in selected_text.lower()
                                )
                            ):
                                return True

                    except Exception:
                        pass

            search_input.press("Escape")

        except Exception as error:
            print(
                f"WARNING selecting {label}: {error}"
            )

        page.wait_for_timeout(500)

    print(
        f"FAILED: could not select {label}: "
        f"{expected_text}"
    )

    return False


def select_country(page):
    print("\nOpening Country...")

    field = page.locator("#country").first

    field.click()
    page.wait_for_timeout(500)

    options = page.locator(
        '[role="option"]:visible'
    )

    for index in range(options.count()):
        option = options.nth(index)

        try:
            text = option.inner_text().strip()

            if text == "India +91":
                option.click()
                page.wait_for_timeout(500)

                print(
                    "Selected Country: India +91"
                )

                return True

        except Exception:
            continue

    print(
        "FAILED: India +91 was not found."
    )

    return False


def select_location(page, location):
    print("\nOpening Location (City)...")

    field = page.locator(
        "#candidate-location"
    ).first

    field.fill(location)

    page.wait_for_timeout(1200)

    options = page.locator(
        '[role="option"]:visible'
    )

    print(
        f"Visible location suggestions: "
        f"{options.count()}"
    )

    for index in range(options.count()):
        try:
            text = options.nth(index).inner_text().strip()

            print(
                f"  {index + 1}. {text}"
            )
        except Exception:
            pass

    for index in range(options.count()):
        option = options.nth(index)

        try:
            text = option.inner_text().strip()

            if location.lower() in text.lower():
                option.click()
                page.wait_for_timeout(500)

                print(
                    f"Selected Location: {text}"
                )

                return True

        except Exception:
            continue

    print(
        "No exact location suggestion found. "
        "Trying broader location..."
    )

    field.fill("")
    page.wait_for_timeout(300)

    field.fill("Jamshedpur, Jharkhand")

    page.wait_for_timeout(1500)

    options = page.locator(
        '[role="option"]:visible'
    )

    print(
        f"Retry suggestions: "
        f"{options.count()}"
    )

    for index in range(options.count()):
        option = options.nth(index)

        try:
            text = option.inner_text().strip()

            if "Jamshedpur" in text:
                option.click()
                page.wait_for_timeout(500)

                print(
                    f"Selected Location: {text}"
                )

                return True

        except Exception:
            continue

    print(
        "WARNING: Could not select location."
    )

    return False


def run_application(package_path):
    print("=" * 80)
    print("JOBAGENT DYNAMIC APPLICATION AUTOFILL")
    print("=" * 80)

    package = load_application_package(package_path)

    job = package["job"]
    candidate = package["candidate"]

    personal = candidate["personal"]
    links = candidate["links"]
    education = candidate["education"]

    experience = candidate["experience"]
    preferences = candidate["preferences"]

    manual_answers = package.get("application", {}).get(
        "manual_answers", {}
    )

    active_offer_deadline = manual_answers.get(
        "active_offer_recruiting_deadline",
        "",
    ).strip()

    application_url = job["url"]

    print("\nAPPROVED APPLICATION")
    print("-" * 80)
    print(f"Company:    {job['company']}")
    print(f"Title:      {job['title']}")
    print(f"Location:   {job['location']}")
    print(f"Score:      {job['match_score']}")
    print(f"URL:        {application_url}")

    print("\nCANDIDATE")
    print("-" * 80)
    print(f"Name:       {personal['full_name']}")
    print(f"Email:      {personal['email']}")
    print(f"Location:   {personal['location']}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False
        )

        page = browser.new_page(
            viewport={
                "width": 1440,
                "height": 1000,
            }
        )

        print("\nOpening approved job...")

        page.goto(
            application_url,
            wait_until="domcontentloaded",
        )

        page.wait_for_timeout(2500)

        print(
            "Job page loaded."
        )

        # --------------------------------------------------------------
        # If this is the normal Stripe job page, click Apply.
        # If Greenhouse embed is already open, continue directly.
        # --------------------------------------------------------------

        if "job-boards.greenhouse.io/embed" not in page.url:
            print(
                "Opening application form..."
            )

            apply_link = page.get_by_role(
                "link",
                name="Apply for this role",
            )

            if apply_link.count() > 0:
                apply_link.click()

                page.wait_for_timeout(
                    2500
                )

            else:
                print(
                    "WARNING: Apply link not found."
                )

        # --------------------------------------------------------------
        # Find Greenhouse application frame.
        # --------------------------------------------------------------

        greenhouse_frame = None

        for frame in page.frames:
            if (
                "job-boards.greenhouse.io/embed/job_app"
                in frame.url
            ):
                greenhouse_frame = frame
                break

        # If application itself is the page, use page.
        if greenhouse_frame is None:
            if (
                "job-boards.greenhouse.io/embed/job_app"
                in page.url
            ):
                form_page = page
            else:
                print(
                    "Could not find Greenhouse application form."
                )

                input(
                    "\nPress Enter to close..."
                )

                browser.close()
                return
        else:
            form_page = greenhouse_frame

        print(
            "Greenhouse application form found."
        )

        form_page.wait_for_timeout(1500)

        # ==============================================================
        # PERSONAL INFORMATION
        # ==============================================================

        print("\n" + "=" * 80)
        print("PERSONAL INFORMATION")
        print("=" * 80)

        full_name = personal["full_name"].strip()

        name_parts = full_name.split(
            maxsplit=1
        )

        first_name = name_parts[0]

        last_name = (
            name_parts[1]
            if len(name_parts) > 1
            else ""
        )

        form_page.locator(
            "#first_name"
        ).fill(first_name)

        form_page.locator(
            "#last_name"
        ).fill(last_name)

        form_page.locator(
            "#email"
        ).fill(personal["email"])

        print(
            "Filled name and email."
        )

        select_country(form_page)

        form_page.locator(
            "#phone"
        ).fill(personal["phone"])

        print("Filled phone.")

        select_location(
            form_page,
            personal["location"],
        )

        # ==============================================================
        # RESUME
        # ==============================================================

        print("\n" + "=" * 80)
        print("RESUME")
        print("=" * 80)

        resume_path = Path(
            package["application"]["resume"]
        ).resolve()

        if resume_path.exists():
            form_page.locator(
                "#resume"
            ).set_input_files(
                str(resume_path)
            )

            print(
                "Uploaded resume:",
                resume_path,
            )

        else:
            print(
                "WARNING: Resume not found:",
                resume_path,
            )

        # ==============================================================
        # EDUCATION
        # ==============================================================

        print("\n" + "=" * 80)
        print("EDUCATION")
        print("=" * 80)

        # School was not available in Greenhouse's dropdown,
        # so use the provided fallback field.
        form_page.locator(
            "#question_67942582"
        ).fill(
            education["institution"]
        )

        print(
            "Filled fallback school:",
            education["institution"],
        )

        degree_ok = select_react_option(
            form_page,
            "#degree--0",
            "Bachelor",
            "Bachelor's Degree",
            "Degree",
            retries=4,
        )

        discipline_ok = select_react_option(
            form_page,
            "#discipline--0",
            "Computer Science",
            "Computer Science",
            "Discipline",
            retries=4,
        )

        form_page.locator(
            "#start-year--0"
        ).fill("2020")

        select_react_option(
            form_page,
            "#end-month--0",
            "August",
            "August",
            "Education end month",
        )

        form_page.locator(
            "#end-year--0"
        ).fill("2023")

        print(
            "Education dates filled."
        )

        # ==============================================================
        # ONLINE PROFILES
        # ==============================================================

        print("\n" + "=" * 80)
        print("ONLINE PROFILES")
        print("=" * 80)

        form_page.locator(
            "#question_67942586"
        ).fill(
            f"GitHub: {links['github']}\n"
            f"LinkedIn: {links['linkedin']}"
        )

        print(
            "Filled GitHub / LinkedIn."
        )

        # ==============================================================
        # APPLICATION QUESTIONS
        # ==============================================================

        print("\n" + "=" * 80)
        print("APPLICATION QUESTIONS")
        print("=" * 80)

        select_react_option(
            form_page,
            "#question_67942591",
            "Yes",
            (
                "Yes, I am currently eligible "
                "to work in the country where "
                "this role is based."
            ),
            "Work authorization",
        )

        select_react_option(
            form_page,
            "#question_67942587",
            "Yes",
            "Yes",
            "WhatsApp recruiting messages",
        )

        # ==============================================================
        # INTERNSHIP AVAILABILITY
        # ==============================================================

        print("\n" + "=" * 80)
        print("INTERNSHIP AVAILABILITY")
        print("=" * 80)

        current_month = datetime.now().month

        internship_options = {
            1: ("January", "January to June (6 months)"),
            5: ("May", "May to July (10 weeks)"),
            6: ("June", "June to August (10 weeks)"),
        }

        if current_month in internship_options:
            month_name, option_text = internship_options[current_month]

            print(
                f"Current month is {month_name}. "
                f"Selecting: {option_text}"
            )

            option = form_page.get_by_text(
                option_text,
                exact=True,
            ).first

            if option.count() > 0:
                try:
                    option.click()
                    print(
                        f"Selected internship availability: "
                        f"{option_text}"
                    )
                except Exception as error:
                    print(
                        "WARNING: Could not select internship "
                        f"availability: {error}"
                    )
            else:
                print(
                    f"WARNING: Internship option not found: "
                    f"{option_text}"
                )
        else:
            month_name = datetime.now().strftime("%B")

            print(
                f"Current month is {month_name}. "
                "No matching cohort option is available."
            )

            print(
                "Leaving internship availability untouched."
            )

        # ==============================================================
        # UNKNOWN / MANUAL FIELDS
        # ==============================================================

        print("\n" + "=" * 80)
        print("FIELDS INTENTIONALLY LEFT MANUAL")
        print("=" * 80)

        if active_offer_deadline:
            form_page.locator(
                "#question_67942589"
            ).fill(active_offer_deadline)

            print(
                "Active offer / recruiting-process deadline: "
                "FILLED FROM SAVED ANSWER"
            )
        else:
            print(
                "Active offer / recruiting-process deadline: BLANK"
            )

        print("GPA: BLANK")
        print("Preferred name: BLANK")
        print("Pronouns: BLANK")
        print("Academic record: BLANK")
        print("Cover letter: BLANK")

        # ==============================================================
        # VERIFY
        # ==============================================================

        print("\n" + "=" * 80)
        print("VERIFYING AUTOFILLED VALUES")
        print("=" * 80)

        select_checks = [
            (
                "#degree--0",
                "Degree",
                "Bachelor's Degree",
            ),
            (
                "#discipline--0",
                "Discipline",
                "Computer Science",
            ),
            (
                "#end-month--0",
                "Education end month",
                "August",
            ),
            (
                "#question_67942591",
                "Work authorization",
                (
                    "Yes, I am currently eligible "
                    "to work in the country where "
                    "this role is based."
                ),
            ),
            (
                "#question_67942592",
                "Visa sponsorship",
                "",
            ),
            (
                "#question_67942587",
                "WhatsApp",
                "Yes",
            ),
        ]

        for selector, label, expected in select_checks:
            actual = get_selected_value(
                form_page,
                selector,
            )

            if actual == expected:
                print(
                    f"[OK] {label}: {actual}"
                )

            elif (
                actual
                and expected.lower()
                in actual.lower()
            ):
                print(
                    f"[OK] {label}: {actual}"
                )

            else:
                print(
                    f"[CHECK] {label}: "
                    f"expected={expected!r}, "
                    f"actual={actual!r}"
                )

        # --------------------------------------------------------------
        # Normal inputs.
        # --------------------------------------------------------------

        normal_checks = [
            (
                "#question_67942589",
                "Active offer / recruiting-process deadline",
                active_offer_deadline,
            ),
            (
                "#first_name",
                "First name",
                first_name,
            ),
            (
                "#last_name",
                "Last name",
                last_name,
            ),
            (
                "#email",
                "Email",
                personal["email"],
            ),
            (
                "#phone",
                "Phone",
                personal["phone"],
            ),
            (
                "#question_67942582",
                "Fallback school",
                education["institution"],
            ),
            (
                "#start-year--0",
                "Education start year",
                "2020",
            ),
            (
                "#end-year--0",
                "Education end year",
                "2023",
            ),
        ]

        for selector, label, expected in normal_checks:
            if selector == "#question_67942589" and not expected:
                print(
                    "[MANUAL] Active offer / recruiting-process deadline: "
                    "no saved answer"
                )
                continue

            try:
                actual = form_page.locator(
                    selector
                ).input_value()

                if actual == expected:
                    print(
                        f"[OK] {label}: {actual}"
                    )

                else:
                    print(
                        f"[CHECK] {label}: "
                        f"expected={expected!r}, "
                        f"actual={actual!r}"
                    )

            except Exception as error:
                print(
                    f"[CHECK] {label}: {error}"
                )

        # ==============================================================
        # EDUCATION RESULT
        # ==============================================================

        print("\n" + "=" * 80)
        print("EDUCATION SELECTION SUMMARY")
        print("=" * 80)

        print(
            "[OK] Bachelor's Degree selected."
            if degree_ok
            else
            "[FAILED] Bachelor's Degree was not verified."
        )

        print(
            "[OK] Computer Science selected."
            if discipline_ok
            else
            "[FAILED] Computer Science was not verified."
        )

        # ==============================================================
        # SCREENSHOT
        # ==============================================================

        print("\n" + "=" * 80)
        print("SCREENSHOT")
        print("=" * 80)

        screenshot_path = (
            "data/applications/"
            f"job_{job['id']}_autofill_validation.png"
        )

        page.screenshot(
            path=screenshot_path,
            full_page=True,
        )

        print(
            "Validation screenshot saved to:",
            screenshot_path,
        )

        # ==============================================================
        # STOP BEFORE SUBMISSION
        # ==============================================================

        print("\n" + "=" * 80)
        print("RESULT")
        print("=" * 80)

        print(
            "DYNAMIC AUTOFILL VALIDATION COMPLETE."
        )

        print("")
        print(
            "NOTHING WAS SUBMITTED."
        )

        print(
            "THE SUBMIT APPLICATION BUTTON "
            "WAS NEVER CLICKED."
        )

        print(
            "No application was sent."
        )

        print(
            "Unknown fields were left untouched."
        )

        print("")
        print(
            "Browser remains open for manual inspection."
        )

        input(
            "\nPress Enter to close the browser..."
        )

        browser.close()


if __name__ == "__main__":
    run_application("data/applications/job_472.json")
