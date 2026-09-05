import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from app.application.answers import save_answer
from app.application.question_resolver import resolve_question


BASE_DIR = Path(__file__).resolve().parents[2]

PROFILE_PATH = (
    BASE_DIR
    / "data"
    / "profile.json"
)

APPLICATIONS_DIR = (
    BASE_DIR
    / "data"
    / "applications"
)

RESUME_PATH = (
    BASE_DIR
    / "data"
    / "resume"
    / "resume.pdf"
)


def load_profile():
    with open(
        PROFILE_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_application():
    application_files = sorted(
        APPLICATIONS_DIR.glob("job_*.json")
    )

    if not application_files:
        raise FileNotFoundError(
            "No application packages found in "
            "data/applications/"
        )

    valid_applications = []

    for application_path in application_files:
        try:
            with open(
                application_path,
                "r",
                encoding="utf-8",
            ) as file:
                application = json.load(file)

        except (json.JSONDecodeError, OSError):
            continue

        job = application.get(
            "job",
            {},
        )

        application_data = application.get(
            "application",
            {},
        )

        url = job.get("url")

        status = application_data.get(
            "status"
        )

        if (
            url
            and status == "ready_for_review"
        ):
            valid_applications.append(
                (
                    application_path,
                    application,
                )
            )

    if not valid_applications:
        raise FileNotFoundError(
            "No ready application package with "
            "a job URL was found."
        )

    # -------------------------------------------------
    # Show all available applications
    # -------------------------------------------------

    print()
    print("=" * 80)
    print("READY APPLICATIONS")
    print("=" * 80)
    print()

    for index, (
        application_path,
        application,
    ) in enumerate(
        valid_applications,
        start=1,
    ):
        job = application.get(
            "job",
            {},
        )

        print(
            f"[{index}] "
            f"{job.get('company', 'Unknown company')} - "
            f"{job.get('title', 'Unknown role')}"
        )

        print(
            f"    Package: {application_path.name}"
        )

        print(
            f"    Location: "
            f"{job.get('location', 'Unknown')}"
        )

        print(
            f"    Match score: "
            f"{job.get('match_score', 'Unknown')}"
        )

        print(
            f"    URL: "
            f"{job.get('url', '')}"
        )

        print()

    # -------------------------------------------------
    # Ask which application to open
    # -------------------------------------------------

    while True:
        choice = input(
            "Select an application number "
            "(or press Enter to cancel): "
        ).strip()

        if not choice:
            raise RuntimeError(
                "Application selection cancelled."
            )

        try:
            selected_index = int(choice)
        except ValueError:
            print(
                "Please enter a valid application number."
            )
            continue

        if not (
            1
            <= selected_index
            <= len(valid_applications)
        ):
            print(
                "Invalid application number."
            )
            continue

        break

    application_path, application = (
        valid_applications[
            selected_index - 1
        ]
    )

    print()
    print(
        f"Using application package: "
        f"{application_path.name}"
    )

    return application


def select_greenhouse_option(
    page,
    field_id,
    option_text,
):
    field = page.locator(
        f"#{field_id}"
    )

    field.click()

    page.wait_for_timeout(300)

    option = page.locator(
        '[role="option"]'
    ).filter(
        has_text=option_text
    ).last

    if option.count() == 0:
        raise RuntimeError(
            f"Could not find option "
            f"{option_text!r} for "
            f"{field_id}"
        )

    option.click()

    page.wait_for_timeout(300)


def clean_question_text(text):
    """
    Clean text extracted from labels or surrounding
    form containers.
    """

    if not text:
        return ""

    lines = []

    for line in text.splitlines():
        line = " ".join(
            line.strip().split()
        )

        if line:
            lines.append(line)

    return " ".join(lines).strip()


def get_surrounding_question_text(
    page,
    control,
):
    """
    Try to recover question text from the DOM
    surrounding a control.

    This is useful for custom application controls
    where there is no normal <label for="...">.
    """

    try:
        result = control.evaluate(
            """
            element => {
                const candidates = [];

                let current = element;

                for (let depth = 0; depth < 6 && current; depth++) {
                    const semantic = current.querySelector(
                        'label, legend, [role="label"], '
                        '[data-qa*="label"], [class*="label"], '
                        '[class*="question"]'
                    );

                    if (semantic && semantic.innerText) {
                        candidates.push(semantic.innerText);
                    }

                    const text = current.innerText || "";

                    if (text.trim()) {
                        candidates.push(text);
                    }

                    current = current.parentElement;
                }

                return candidates;
            }
            """
        )

    except Exception:
        return ""

    if not result:
        return ""

    field_id = control.get_attribute(
        "id"
    )

    for text in result:

        cleaned = clean_question_text(
            text
        )

        if not cleaned:
            continue

        if field_id:
            cleaned = cleaned.replace(
                field_id,
                "",
            ).strip()

        if cleaned:
            return cleaned

    return ""


def get_question_label(
    page,
    control,
):
    """
    Determine the human-readable question associated
    with a form control.

    Order:

    1. Explicit <label for="...">
    2. aria-label
    3. placeholder
    4. aria-labelledby
    5. Surrounding form/container text
    6. Fallback field identifier
    """

    field_id = control.get_attribute(
        "id"
    )

    label_text = ""

    # -------------------------------------------------
    # 1. Explicit HTML label
    # -------------------------------------------------

    if field_id:

        label = page.locator(
            f'label[for="{field_id}"]'
        )

        if label.count() > 0:

            try:
                label_text = (
                    label.first
                    .inner_text()
                    .strip()
                )

            except Exception:
                label_text = ""

    # -------------------------------------------------
    # 2. aria-label
    # -------------------------------------------------

    if not label_text:

        label_text = (
            control.get_attribute(
                "aria-label"
            )
            or ""
        ).strip()

    # -------------------------------------------------
    # 3. placeholder
    # -------------------------------------------------

    if not label_text:

        label_text = (
            control.get_attribute(
                "placeholder"
            )
            or ""
        ).strip()

    # -------------------------------------------------
    # 4. aria-labelledby
    # -------------------------------------------------

    if not label_text:

        labelled_by = (
            control.get_attribute(
                "aria-labelledby"
            )
            or ""
        ).strip()

        if labelled_by:

            parts = []

            for label_id in labelled_by.split():

                element = page.locator(
                    f"#{label_id}"
                )

                if element.count() == 0:
                    continue

                try:
                    text = (
                        element.first
                        .inner_text()
                        .strip()
                    )

                except Exception:
                    text = ""

                if text:
                    parts.append(text)

            label_text = " ".join(parts)

    # -------------------------------------------------
    # 5. Surrounding container
    # -------------------------------------------------

    if not label_text:

        label_text = (
            get_surrounding_question_text(
                page,
                control,
            )
        )

    # -------------------------------------------------
    # 6. Fallback
    # -------------------------------------------------

    if not label_text:

        label_text = (
            f"Unknown field: {field_id}"
        )

    return clean_question_text(
        label_text
    )


def get_field_type(control):
    field_type = (
        control.get_attribute(
            "type"
        )
    )

    if field_type:
        return field_type.lower()

    try:
        tag_name = control.evaluate(
            "element => element.tagName.toLowerCase()"
        )

        return tag_name.lower()

    except Exception:
        return ""


def is_required_control(control):
    required = (
        control.get_attribute(
            "required"
        )
        is not None
    )

    if not required:

        required = (
            control.get_attribute(
                "aria-required"
            )
            == "true"
        )

    return required


def get_control_required_state(control):
    """Determine required state for native and Greenhouse custom controls."""
    if is_required_control(control):
        return True

    try:
        return bool(control.evaluate("""
            element => {
                let node = element;
                for (let depth = 0; depth < 4 && node; depth++) {
                    if (node.getAttribute('required') !== null) return true;
                    if (node.getAttribute('aria-required') === 'true') return true;
                    const text = (node.innerText || '').trim();
                    if (/\\*\\s*$/.test(text)) return true;
                    node = node.parentElement;
                }
                return false;
            }
        """))
    except Exception:
        return False


def is_non_question_control(field_id, field_type):
    """Exclude standard profile/upload controls from generic question scanning."""
    standard_ids = {
        "first_name",
        "last_name",
        "preferred_name",
        "email",
        "country",
        "phone",
        "resume",
        "cover_letter",
    }

    if field_id in standard_ids:
        return True

    return field_type in {
        "hidden",
        "submit",
        "file",
        "button",
    }


def is_safe_for_saved_text_answer(control):
    """
    Only allow saved answers to be automatically
    inserted into normal text-like fields.

    Custom dropdowns/radios are intentionally excluded
    until their interaction can be handled safely.
    """

    field_type = get_field_type(
        control
    )

    return field_type in {
        "text",
        "email",
        "tel",
        "url",
        "search",
        "number",
        "textarea",
    }


def is_custom_control(control):
    """
    Detect controls that are likely implemented through
    a custom UI rather than a normal text field.
    """

    field_type = get_field_type(
        control
    )

    if field_type in {
        "checkbox",
        "radio",
    }:
        return True

    role = (
        control.get_attribute(
            "role"
        )
        or ""
    ).lower()

    if role in {
        "combobox",
        "listbox",
        "option",
        "radio",
        "switch",
    }:
        return True

    if control.get_attribute("aria-haspopup"):
        return True

    if control.get_attribute("readonly") is not None:
        return True

    # Greenhouse custom selects often render as a text input
    # with a nearby toggle button instead of a native <select>.
    try:
        has_nearby_button = control.evaluate(
            """
            element => {
                const parent = element.parentElement;
                if (!parent) return false;

                return !!parent.querySelector(
                    'button, [role="button"], [aria-haspopup]'
                );
            }
            """
        )

        if has_nearby_button:
            return True

    except Exception:
        pass

    return field_type in {
        "button",
    }


def is_sensitive_question(question):
    """
    Questions involving legal/work authorization,
    sponsorship, immigration, or similar topics must
    never be answered automatically by JobAgent.
    """

    question_lower = (
        question.lower()
    )

    sensitive_keywords = [
        "work authorization",
        "authorized to work",
        "legally authorized",
        "visa",
        "sponsorship",
        "immigration",
        "immigration status",
        "citizenship",
        "citizen",
        "work permit",
        "employment authorization",
    ]

    return any(
        keyword in question_lower
        for keyword in sensitive_keywords
    )


def ask_user_for_answer(question):
    print()
    print("=" * 80)
    print("USER INPUT REQUIRED")
    print("=" * 80)

    print()
    print("Application question:")
    print(question)

    print()

    if is_sensitive_question(
        question
    ):

        print(
            "This question may involve legal or "
            "work-authorization information."
        )

        print(
            "JobAgent will NOT guess this answer."
        )

    print()

    while True:

        answer = input(
            "Your answer (leave blank to skip): "
        ).strip()

        if answer:
            return answer

        print(
            "No answer entered."
        )

        confirm = input(
            "Skip this question? [y/N]: "
        ).strip().lower()

        if confirm == "y":
            return None


def normalize_question_text(text):
    return " ".join(
        (text or "")
        .lower()
        .strip()
        .split()
    )


def find_application_control_by_question(
    page,
    question_text,
):
    """Find a visible application control by its rendered question/label text."""
    target = normalize_question_text(
        question_text
    )

    controls = page.locator(
        'input, textarea, select, [role="combobox"], '
        '[role="listbox"], [role="radio"], [role="switch"]'
    )

    for i in range(
        controls.count()
    ):

        control = controls.nth(i)

        try:

            if not control.is_visible():
                continue

            field_id = control.get_attribute(
                "id"
            )

            field_type = get_field_type(
                control
            )

            if (
                not field_id
                or is_non_question_control(
                    field_id,
                    field_type,
                )
            ):
                continue

            question = get_question_label(
                page,
                control,
            )

            if (
                normalize_question_text(
                    question
                )
                == target
            ):
                return control

        except Exception:
            continue

    return None


def require_application_control(
    page,
    question_text,
):
    control = find_application_control_by_question(
        page,
        question_text,
    )

    if control is None:
        raise RuntimeError(
            f'Could not find application question: '
            f'"{question_text}"'
        )

    return control


def get_control_id(control):
    return control.get_attribute(
        "id"
    )


def get_safe_profile_answer(
    question,
    profile,
):
    """
    Return an answer only when it can be derived directly from
    explicit, non-sensitive profile facts.

    This function is intentionally conservative. It does not infer
    legal/work-authorization answers, salary expectations, availability,
    or other facts that are not explicitly represented in the profile.
    """

    if (
        not question
        or is_sensitive_question(question)
    ):
        return None

    q = normalize_question_text(
        question
    )

    skills = {
        normalize_question_text(skill)
        for skill in profile.get(
            "skills",
            [],
        )
    }

    experience = profile.get(
        "experience",
        [],
    )

    professional_years = profile.get(
        "years_of_experience"
    )

    location = profile.get(
        "location",
        "",
    )

    target_roles = [
        normalize_question_text(role)
        for role in profile.get(
            "target_roles",
            [],
        )
    ]

    preferences = profile.get(
        "application_preferences",
        {},
    )

    # Explicit React/Next.js experience from skills + professional history.
    if (
        (
            "react" in q
            or "react.js" in q
            or "reactjs" in q
            or "next.js" in q
            or "nextjs" in q
        )
        and any(
            phrase in q
            for phrase in (
                "experience",
                "worked with",
                "work with",
                "using",
                "proficient",
                "familiar",
                "knowledge",
            )
        )
    ):

        if (
            "react.js" in skills
            or "next.js" in skills
            or "react" in skills
            or "typescript" in skills
        ):

            has_web_experience = any(
                normalize_question_text(
                    item.get(
                        "role",
                        "",
                    )
                )
                in {
                    "web developer intern",
                    "web developer",
                }
                for item in experience
            )

            if has_web_experience:
                return (
                    "Yes, I have professional experience building "
                    "web applications with React and Next.js."
                )

    # Explicit years-of-experience question.
    if (
        professional_years is not None
        and any(
            phrase in q
            for phrase in (
                "how many years",
                "years of experience",
                "years' experience",
                "years experience",
            )
        )
        and any(
            phrase in q
            for phrase in (
                "professional",
                "work experience",
                "experience",
            )
        )
    ):
        return str(
            professional_years
        )

    # Explicit current-location questions.
    if (
        location
        and any(
            phrase in q
            for phrase in (
                "where are you currently located",
                "current location",
                "where do you live",
                "where are you located",
            )
        )
    ):
        return location

    # Explicit relocation preference.
    if (
        "relocat" in q
        and preferences.get(
            "willing_to_relocate"
        )
        is True
    ):
        return "Yes"

    # Explicit five-day office preference.
    if (
        preferences.get(
            "okay_with_five_day_office"
        )
        is True
        and "5 days a week" in q
        and any(
            phrase in q
            for phrase in (
                "office",
                "work from the office",
                "working from the office",
            )
        )
    ):
        return "Yes"

    # Explicit education facts.
    education = profile.get(
        "education",
        []
    )

    if (
        education
        and any(
            phrase in q
            for phrase in (
                "computer science degree",
                "degree in computer science",
                "studied computer science",
                "computer science education",
            )
        )
    ):

        has_cs_degree = any(
            "computer science"
            in normalize_question_text(
                item.get(
                    "degree",
                    "",
                )
            )
            for item in education
        )

        if has_cs_degree:
            return "Yes"

    # Explicit target-role interest.
    if any(
        phrase in q
        for phrase in (
            "interested in this role",
            "interested in the role",
            "interested in this position",
        )
    ):

        if target_roles:
            return "Yes"

    return None


def process_application_questions(
    page,
    profile,
    handled_question_ids=None,
):
    """
    Process application questions after known fields
    have been filled.

    Flow:

    1. Known field -> already handled.
    2. Saved answer -> automatically fill when safe.
    3. Unknown required text field -> ask user.
    4. Unknown required custom control -> report it.
    5. Unknown optional field -> leave untouched.
    6. Never guess legal/work authorization answers.
    """

    known_question_ids = set(
        handled_question_ids or set()
    )

    reusable_answers = []
    filled_answers = []
    asked_questions = []
    skipped_questions = []
    unknown_required = []
    custom_controls = []
    handled_questions = []

    controls = page.locator(
        'input, textarea, select, button, '
        '[role="combobox"], [role="listbox"], '
        '[role="radio"], [role="switch"]'
    )

    for i in range(
        controls.count()
    ):

        control = controls.nth(i)

        if not control.is_visible():
            continue

        field_id = control.get_attribute(
            "id"
        )

        if not field_id:
            continue

        field_type = get_field_type(
            control
        )

        custom = is_custom_control(
            control
        )

        # Standard profile/upload controls are not application questions.
        if is_non_question_control(
            field_id,
            field_type,
        ):
            continue

        question = get_question_label(
            page,
            control,
        )

        # Fields explicitly handled in main() are already complete.
        if field_id in known_question_ids:

            if field_id.startswith(
                "question_"
            ):

                required = get_control_required_state(
                    control
                )

                handled_questions.append(
                    {
                        "id": field_id,
                        "question": question,
                        "type": field_type,
                        "custom": custom,
                        "required": required,
                    }
                )

            continue

        if custom:

            custom_controls.append(
                {
                    "id": field_id,
                    "question": question,
                    "type": field_type,
                }
            )

        resolution = resolve_question(
            question
        )

        answer = resolution.answer
        answer_source = resolution.source

        # -------------------------------------------------
        # Existing reusable or explicit profile answer
        # -------------------------------------------------

        if (
            resolution.status == "ANSWER"
            and answer is not None
        ):

            if answer_source == "saved":

                reusable_answers.append(
                    {
                        "id": field_id,
                        "question": question,
                        "answer": answer,
                        "type": field_type,
                        "custom": custom,
                    }
                )

            else:

                print()
                print(
                    "SAFE PROFILE ANSWER FOUND:"
                )

                print(
                    f"Question: {question}"
                )

                print(
                    f"Answer: {answer}"
                )

                print(
                    "Source: explicit profile facts"
                )

            if is_safe_for_saved_text_answer(
                control
            ):

                try:

                    control.fill(
                        answer
                    )

                    filled_answers.append(
                        {
                            "id": field_id,
                            "question": question,
                            "answer": answer,
                            "source": answer_source,
                        }
                    )

                    if answer_source == "profile":

                        save_answer(
                            question,
                            answer,
                        )

                except Exception as error:

                    print()
                    print(
                        f"Could not automatically "
                        f"fill saved answer for "
                        f"{field_id}: {error}"
                    )

            else:

                print()
                print(
                    "Saved answer found for a "
                    "custom/non-text control."
                )

                print(
                    f"Question: {question}"
                )

                print(
                    f"Saved answer: {answer}"
                )

                print(
                    "JobAgent will not interact "
                    "with this control automatically."
                )

            continue

        # -------------------------------------------------
        # No safe answer available
        # -------------------------------------------------

        required = get_control_required_state(
            control
        )

        if not required:
            continue

        # -------------------------------------------------
        # Unknown required question
        # -------------------------------------------------

        unknown_required.append(
            {
                "id": field_id,
                "question": question,
                "type": field_type,
                "custom": custom,
            }
        )

        if resolution.reason:

            print()
            print(
                f"Reason: {resolution.reason}"
            )

        # -------------------------------------------------
        # Normal text question
        # -------------------------------------------------

        if is_safe_for_saved_text_answer(
            control
        ):

            answer = ask_user_for_answer(
                question
            )

            asked_questions.append(
                {
                    "id": field_id,
                    "question": question,
                    "answer": answer,
                }
            )

            if answer is None:

                skipped_questions.append(
                    {
                        "id": field_id,
                        "question": question,
                    }
                )

                continue

            save_answer(
                question,
                answer,
            )

            try:

                # Re-resolve the exact control by its ID before filling.
                # This avoids stale/broad Playwright locators when the
                # application page has dynamic form controls.
                fill_control = page.locator(
                    f"#{field_id}"
                )

                if not fill_control.is_visible():
                    raise RuntimeError(
                        f"Application control "
                        f"#{field_id} is not visible."
                    )

                fill_control.fill(
                    answer
                )

                filled_answers.append(
                    {
                        "id": field_id,
                        "question": question,
                        "answer": answer,
                    }
                )

            except Exception as error:

                print()
                print(
                    f"Could not fill your answer "
                    f"into {field_id}: {error}"
                )

            continue

        # -------------------------------------------------
        # Unknown custom question
        # -------------------------------------------------

        print()
        print(
            "UNKNOWN REQUIRED CUSTOM CONTROL"
        )

        print(
            f"Field: {field_id}"
        )

        print(
            f"Question: {question}"
        )

        print(
            f"Type: {field_type}"
        )

        print(
            "JobAgent will not guess how to "
            "interact with this control."
        )

    return {
        "reusable_answers": reusable_answers,
        "filled_answers": filled_answers,
        "asked_questions": asked_questions,
        "skipped_questions": skipped_questions,
        "unknown_required": unknown_required,
        "custom_controls": custom_controls,
        "handled_questions": handled_questions,
    }


def get_control_value(
    control,
):
    """
    Read the current browser value of a form control.

    For normal inputs/textareas this returns the input value.
    For custom controls it also checks text/ARIA state.
    """

    try:

        value = control.input_value(
            timeout=2000
        )

        if value is not None:
            return value.strip()

    except Exception:
        pass

    for attribute in (
        "value",
        "aria-valuetext",
        "aria-label",
    ):

        try:

            value = control.get_attribute(
                attribute
            )

            if value:
                return value.strip()

        except Exception:
            pass

    try:

        text = control.inner_text(
            timeout=2000
        )

        if text:
            return " ".join(
                text.strip().split()
            )

    except Exception:
        pass

    return ""


def verify_text_control(
    page,
    field_id,
    expected,
    label,
):
    """
    Verify that a normal text-like browser control
    contains the expected value.
    """

    control = page.locator(
        f"#{field_id}"
    )

    if control.count() == 0:
        return {
            "label": label,
            "field": field_id,
            "status": "FAIL",
            "expected": expected,
            "actual": "",
            "reason": "Control not found",
        }

    try:

        if not control.is_visible():
            return {
                "label": label,
                "field": field_id,
                "status": "FAIL",
                "expected": expected,
                "actual": "",
                "reason": "Control is not visible",
            }

    except Exception as error:

        return {
            "label": label,
            "field": field_id,
            "status": "FAIL",
            "expected": expected,
            "actual": "",
            "reason": str(error),
        }

    actual = get_control_value(
        control
    )

    expected_normalized = (
        str(expected)
        .strip()
    )

    actual_normalized = (
        str(actual)
        .strip()
    )

    if actual_normalized == expected_normalized:

        return {
            "label": label,
            "field": field_id,
            "status": "PASS",
            "expected": expected_normalized,
            "actual": actual_normalized,
            "reason": "",
        }

    return {
        "label": label,
        "field": field_id,
        "status": "FAIL",
        "expected": expected_normalized,
        "actual": actual_normalized,
        "reason": "Browser value does not match expected value",
    }


def verify_custom_option(
    page,
    field_id,
    expected_option,
    label,
):
    """
    Verify a Greenhouse-style custom select by inspecting
    the associated control and nearby rendered text.

    We intentionally do not click anything during verification.
    """

    control = page.locator(
        f"#{field_id}"
    )

    if control.count() == 0:

        return {
            "label": label,
            "field": field_id,
            "status": "FAIL",
            "expected": expected_option,
            "actual": "",
            "reason": "Control not found",
        }

    try:

        if not control.is_visible():

            return {
                "label": label,
                "field": field_id,
                "status": "FAIL",
                "expected": expected_option,
                "actual": "",
                "reason": "Control is not visible",
            }

    except Exception as error:

        return {
            "label": label,
            "field": field_id,
            "status": "FAIL",
            "expected": expected_option,
            "actual": "",
            "reason": str(error),
        }

    values = []

    control_value = get_control_value(
        control
    )

    if control_value:
        values.append(
            control_value
        )

    try:

        parent_text = control.evaluate(
            """
            element => {
                const parent = element.parentElement;
                return parent ? (parent.innerText || '') : '';
            }
            """
        )

        if parent_text:
            values.append(
                " ".join(
                    parent_text
                    .strip()
                    .split()
                )
            )

    except Exception:
        pass

    try:

        container_text = control.evaluate(
            """
            element => {
                let node = element;

                for (let depth = 0; depth < 4 && node; depth++) {
                    const text = (node.innerText || '').trim();

                    if (text) {
                        return text;
                    }

                    node = node.parentElement;
                }

                return '';
            }
            """
        )

        if container_text:
            values.append(
                " ".join(
                    container_text
                    .strip()
                    .split()
                )
            )

    except Exception:
        pass

    expected_normalized = normalize_question_text(
        expected_option
    )

    for value in values:

        value_normalized = normalize_question_text(
            value
        )

        if expected_normalized in value_normalized:

            return {
                "label": label,
                "field": field_id,
                "status": "PASS",
                "expected": expected_option,
                "actual": value,
                "reason": "",
            }

    actual = values[0] if values else ""

    return {
        "label": label,
        "field": field_id,
        "status": "FAIL",
        "expected": expected_option,
        "actual": actual,
        "reason": "Expected option was not found in the rendered control state",
    }


def verify_file_control(
    page,
    field_id,
    expected_filename,
    label,
):
    """
    Verify that the expected file is attached to the application.

    Greenhouse removes/replaces the original file input after a
    successful upload. Therefore verification checks both:

    1. Current input[type=file] controls.
    2. Greenhouse's visible .file-upload__filename element.

    The upload is considered verified only when the expected filename
    is actually present in one of these states.
    """

    expected_filename = Path(
        expected_filename
    ).name

    # -------------------------------------------------
    # 1. Inspect current file input controls
    # -------------------------------------------------

    file_inputs = page.locator(
        'input[type="file"]'
    )

    all_files = []

    for index in range(file_inputs.count()):
        control = file_inputs.nth(index)

        try:
            files = control.evaluate(
                """
                element => Array.from(
                    element.files || []
                ).map(
                    file => file.name
                )
                """
            )
        except Exception:
            files = []

        if files:
            all_files.extend(files)

    # -------------------------------------------------
    # 2. Inspect Greenhouse visible uploaded filename
    # -------------------------------------------------

    visible_filenames = []

    filename_elements = page.locator(
        ".file-upload__filename"
    )

    for index in range(
        filename_elements.count()
    ):
        element = filename_elements.nth(index)

        try:
            if not element.is_visible():
                continue

            text = (
                element.inner_text()
                or ""
            ).strip()

            if text:
                visible_filenames.append(
                    text
                )

        except Exception:
            continue

    # -------------------------------------------------
    # 3. Combine verified filenames
    # -------------------------------------------------

    discovered_files = []

    for filename in (
        all_files + visible_filenames
    ):
        filename = Path(
            filename
        ).name

        if filename and filename not in discovered_files:
            discovered_files.append(
                filename
            )

    # -------------------------------------------------
    # 4. Expected resume found
    # -------------------------------------------------

    if expected_filename in discovered_files:
        return {
            "label": label,
            "field": field_id,
            "status": "PASS",
            "expected": expected_filename,
            "actual": ", ".join(
                discovered_files
            ),
            "reason": "",
        }

    # -------------------------------------------------
    # 5. Nothing found
    # -------------------------------------------------

    if not discovered_files:
        return {
            "label": label,
            "field": field_id,
            "status": "FAIL",
            "expected": expected_filename,
            "actual": "",
            "reason": "No uploaded filename could be verified",
        }

    # -------------------------------------------------
    # 6. Wrong/unexpected file found
    # -------------------------------------------------

    return {
        "label": label,
        "field": field_id,
        "status": "FAIL",
        "expected": expected_filename,
        "actual": ", ".join(
            discovered_files
        ),
        "reason": "Expected file was not attached",
    }


def verify_required_question_state(
    page,
    handled_questions,
):
    """
    Verify that every required known question has some
    non-empty browser state.

    This is deliberately conservative: it does not decide
    whether the answer is semantically correct. It only
    verifies that the required control is populated/selected.
    """

    verification = []

    for item in handled_questions:

        if not item.get(
            "required"
        ):
            continue

        field_id = item.get(
            "id"
        )

        question = item.get(
            "question",
            field_id,
        )

        control = page.locator(
            f"#{field_id}"
        )

        if control.count() == 0:

            verification.append(
                {
                    "label": question,
                    "field": field_id,
                    "status": "FAIL",
                    "expected": "non-empty required control",
                    "actual": "",
                    "reason": "Required control not found",
                }
            )

            continue

        actual = get_control_value(
            control
        )

        if actual:

            verification.append(
                {
                    "label": question,
                    "field": field_id,
                    "status": "PASS",
                    "expected": "non-empty required control",
                    "actual": actual,
                    "reason": "",
                }
            )

        else:

            # For custom controls, inspect nearby rendered state.
            try:

                rendered = control.evaluate(
                    """
                    element => {
                        let node = element;

                        for (let depth = 0; depth < 4 && node; depth++) {
                            const text = (node.innerText || '').trim();

                            if (text) {
                                return text;
                            }

                            node = node.parentElement;
                        }

                        return '';
                    }
                    """
                )

            except Exception:
                rendered = ""

            if rendered:

                verification.append(
                    {
                        "label": question,
                        "field": field_id,
                        "status": "PASS",
                        "expected": "non-empty required control",
                        "actual": rendered,
                        "reason": "",
                    }
                )

            else:

                verification.append(
                    {
                        "label": question,
                        "field": field_id,
                        "status": "FAIL",
                        "expected": "non-empty required control",
                        "actual": "",
                        "reason": "Required control appears empty",
                    }
                )

    return verification


def verify_application_state(
    page,
    profile,
    handled_questions,
):
    """
    Verify the browser state after all autofill actions.

    This function performs read-only verification.
    It never clicks or changes application controls.
    """

    verification = []

    print()
    print("=" * 80)
    print("APPLICATION STATE VERIFICATION")
    print("=" * 80)

    first_name = profile[
        "name"
    ].split()[0]

    last_name = " ".join(
        profile["name"].split()[1:]
    )

    verification.append(
        verify_text_control(
            page,
            "first_name",
            first_name,
            "First Name",
        )
    )

    verification.append(
        verify_text_control(
            page,
            "last_name",
            last_name,
            "Last Name",
        )
    )

    verification.append(
        verify_text_control(
            page,
            "preferred_name",
            first_name,
            "Preferred First Name",
        )
    )

    verification.append(
        verify_text_control(
            page,
            "email",
            profile["email"],
            "Email",
        )
    )

    verification.append(
        verify_text_control(
            page,
            "phone",
            profile["phone"],
            "Phone",
        )
    )

    verification.append(
        verify_text_control(
            page,
            "question_5428816009",
            profile["linkedin"],
            "LinkedIn Profile",
        )
    )

    portfolio = profile.get(
        "portfolio",
        "",
    )

    if portfolio:

        verification.append(
            verify_text_control(
                page,
                "question_5428817009",
                portfolio,
                "Website",
            )
        )

        verification.append(
            verify_text_control(
                page,
                "question_5428819009",
                portfolio,
                "Portfolio",
            )
        )

    verification.append(
        verify_text_control(
            page,
            "question_5428818009",
            profile["github"],
            "GitHub",
        )
    )

    verification.append(
        verify_text_control(
            page,
            "question_5428821009",
            profile["location"],
            "Current Location",
        )
    )

    verification.append(
        verify_file_control(
            page,
            "resume",
            RESUME_PATH.name,
            "Resume",
        )
    )

    # The Eudia form uses Greenhouse custom controls for these
    # questions. Verify them without clicking.
    preferences = profile.get(
        "application_preferences",
        {},
    )

    if (
        preferences.get(
            "okay_with_five_day_office"
        )
        is True
    ):

        verification.append(
            verify_custom_option(
                page,
                "question_5428820009",
                "Yes",
                "5-day office",
            )
        )

    if (
        preferences.get(
            "willing_to_relocate"
        )
        is True
    ):

        verification.append(
            verify_custom_option(
                page,
                "question_5428822009",
                "Yes",
                "Relocation",
            )
        )

    required_verification = (
        verify_required_question_state(
            page,
            handled_questions,
        )
    )

    verification.extend(
        required_verification
    )

    print()

    passed = 0
    failed = 0

    for item in verification:

        if item["status"] == "PASS":
            passed += 1
            marker = "PASS"
        else:
            failed += 1
            marker = "FAIL"

        print(
            f"[{marker}] {item['label']}"
        )

        if item.get("expected"):
            print(
                f"  Expected: {item['expected']}"
            )

        if item.get("actual"):
            print(
                f"  Actual:   {item['actual']}"
            )

        if item.get("reason"):
            print(
                f"  Reason:   {item['reason']}"
            )

        print()

    print(
        f"Verification checks passed: {passed}"
    )

    print(
        f"Verification checks failed: {failed}"
    )

    verification_passed = (
        failed == 0
    )

    if verification_passed:

        print()
        print(
            "APPLICATION STATE VERIFICATION: PASSED"
        )

        print(
            "All verified fields contain the expected values."
        )

    else:

        print()
        print(
            "APPLICATION STATE VERIFICATION: FAILED"
        )

        print(
            "The application must be reviewed before submission."
        )

    return {
        "passed": verification_passed,
        "checks": verification,
        "passed_count": passed,
        "failed_count": failed,
    }


def print_question_results(
    results
):
    print()
    print("=" * 80)
    print("APPLICATION QUESTION RESULTS")
    print("=" * 80)

    reusable_answers = results[
        "reusable_answers"
    ]

    filled_answers = results[
        "filled_answers"
    ]

    asked_questions = results[
        "asked_questions"
    ]

    skipped_questions = results[
        "skipped_questions"
    ]

    unknown_required = results[
        "unknown_required"
    ]

    custom_controls = results[
        "custom_controls"
    ]

    handled_questions = results[
        "handled_questions"
    ]

    if handled_questions:

        print()
        print(
            "KNOWN APPLICATION QUESTIONS HANDLED:"
        )

        print()

        for item in handled_questions:

            print(
                f"- Field: {item['id']}"
            )

            print(
                f"  Question: "
                f"{item['question']}"
            )

            print(
                f"  Type: "
                f"{item['type']}"
            )

            if item["custom"]:

                print(
                    "  Control: custom"
                )

            print(
                f"  Required: "
                f"{'Yes' if item['required'] else 'No'}"
            )

            print(
                "  Status: already handled"
            )

            print()

    if reusable_answers:

        print()
        print(
            "REUSABLE ANSWERS FOUND:"
        )

        print()

        for item in reusable_answers:

            print(
                f"- Field: {item['id']}"
            )

            print(
                f"  Question: "
                f"{item['question']}"
            )

            print(
                f"  Saved answer: "
                f"{item['answer']}"
            )

            print(
                f"  Type: {item['type']}"
            )

            if item["custom"]:

                print(
                    "  Control: custom"
                )

            print()

    else:

        print()
        print(
            "No reusable answers found."
        )

    if filled_answers:

        print()
        print(
            "ANSWERS FILLED INTO FORM:"
        )

        print()

        for item in filled_answers:

            print(
                f"- {item['question']}"
            )

            print(
                f"  Answer: "
                f"{item['answer']}"
            )

            print()

    if asked_questions:

        print()
        print(
            "NEW ANSWERS PROVIDED BY USER:"
        )

        print()

        for item in asked_questions:

            if item["answer"] is None:

                print(
                    f"- Skipped: "
                    f"{item['question']}"
                )

            else:

                print(
                    f"- {item['question']}"
                )

                print(
                    f"  Saved answer: "
                    f"{item['answer']}"
                )

            print()

    if skipped_questions:

        print()
        print(
            "QUESTIONS SKIPPED:"
        )

        print()

        for item in skipped_questions:

            print(
                f"- {item['question']}"
            )

            print()

    if custom_controls:

        print()
        print(
            "CUSTOM CONTROLS DETECTED:"
        )

        print()

        for item in custom_controls:

            print(
                f"- Field: {item['id']}"
            )

            print(
                f"  Type: {item['type']}"
            )

            print(
                f"  Question: "
                f"{item['question']}"
            )

            print()

    if unknown_required:

        print()
        print(
            "REQUIRED QUESTIONS DETECTED:"
        )

        print()

        for question in unknown_required:

            print(
                f"- Field: "
                f"{question['id']}"
            )

            print(
                f"  Type: "
                f"{question['type']}"
            )

            print(
                f"  Question: "
                f"{question['question']}"
            )

            if question["custom"]:

                print(
                    "  Control: custom"
                )

            print()

    else:

        print()
        print(
            "No unknown required questions detected."
        )

    print()

    print(
        f"Known application questions handled: "
        f"{len(handled_questions)}"
    )

    print(
        f"Reusable answers found: "
        f"{len(reusable_answers)}"
    )

    profile_answers_filled = sum(
        1
        for item in filled_answers
        if item.get("source") == "profile"
    )

    print(
        f"Profile-derived answers filled: "
        f"{profile_answers_filled}"
    )

    print(
        f"Answers filled: "
        f"{len(filled_answers)}"
    )

    print(
        f"Questions asked: "
        f"{len(asked_questions)}"
    )

    print(
        f"Questions skipped: "
        f"{len(skipped_questions)}"
    )

    print(
        f"Custom controls detected: "
        f"{len(custom_controls)}"
    )

    required_handled = sum(
        1
        for item in handled_questions
        if item.get("required")
    )

    print(
        f"Required questions detected: "
        f"{required_handled + len(unknown_required)}"
    )

    print(
        f"Required known questions handled: "
        f"{required_handled}"
    )


def main():
    profile = load_profile()
    application = load_application()

    job = application.get(
        "job",
        {}
    )

    application_url = job.get(
        "url"
    )

    if not application_url:
        raise ValueError(
            "Application package does not contain "
            "a job URL."
        )

    first_name = profile[
        "name"
    ].split()[0]

    last_name = " ".join(
        profile["name"].split()[1:]
    )

    print()
    print("=" * 80)
    print(
        "JOBAGENT APPLICATION AUTOFILL"
    )
    print("=" * 80)

    print()

    print(
        f"Company: "
        f"{job.get('company', 'Unknown')}"
    )

    print(
        f"Role: "
        f"{job.get('title', 'Unknown')}"
    )

    print(
        f"URL: {application_url}"
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        print()
        print(
            "Opening application..."
        )

        page.goto(
            application_url,
            wait_until="domcontentloaded",
        )

        page.wait_for_timeout(
            3000
        )

        print(
            f"Page: {page.title()}"
        )

        print()
        print(
            "Filling personal information..."
        )

        page.locator(
            "#first_name"
        ).fill(
            first_name
        )

        page.locator(
            "#last_name"
        ).fill(
            last_name
        )

        page.locator(
            "#preferred_name"
        ).fill(
            first_name
        )

        page.locator(
            "#email"
        ).fill(
            profile["email"]
        )

        page.locator(
            "#phone"
        ).fill(
            profile["phone"]
        )

        print(
            "Setting country: India"
        )

        select_greenhouse_option(
            page,
            "country",
            "India +91",
        )

        print(
            "Uploading resume..."
        )

        if not RESUME_PATH.exists():

            raise FileNotFoundError(
                f"Resume not found: "
                f"{RESUME_PATH}"
            )

        page.locator(
            "#resume"
        ).set_input_files(
            str(RESUME_PATH)
        )

        print(
            "Filling LinkedIn, GitHub and portfolio..."
        )

        handled_question_ids = set()

        linkedin_control = require_application_control(
            page,
            "LinkedIn Profile",
        )

        linkedin_control.fill(
            profile["linkedin"]
        )

        handled_question_ids.add(
            get_control_id(
                linkedin_control
            )
        )

        github_control = require_application_control(
            page,
            "GitHub",
        )

        github_control.fill(
            profile["github"]
        )

        handled_question_ids.add(
            get_control_id(
                github_control
            )
        )

        portfolio = profile.get(
            "portfolio",
            "",
        )

        if portfolio:

            website_control = require_application_control(
                page,
                "Website",
            )

            website_control.fill(
                portfolio
            )

            handled_question_ids.add(
                get_control_id(
                    website_control
                )
            )

            portfolio_control = require_application_control(
                page,
                "Portfolio",
            )

            portfolio_control.fill(
                portfolio
            )

            handled_question_ids.add(
                get_control_id(
                    portfolio_control
                )
            )

        print(
            "Setting current location..."
        )

        location_control = require_application_control(
            page,
            "Where are you currently located?",
        )

        location_control.fill(
            profile["location"]
        )

        handled_question_ids.add(
            get_control_id(
                location_control
            )
        )

        preferences = profile.get(
            "application_preferences",
            {},
        )

        office_preference = preferences.get(
            "okay_with_five_day_office"
        )

        if office_preference is True:

            print(
                "Setting 5-day office: Yes"
            )

            office_control = require_application_control(
                page,
                "Are you okay with working from the office location stated in this job posting 5 days a week?*",
            )

            select_greenhouse_option(
                page,
                get_control_id(
                    office_control
                ),
                "Yes",
            )

            handled_question_ids.add(
                get_control_id(
                    office_control
                )
            )

        relocation_preference = preferences.get(
            "willing_to_relocate"
        )

        if relocation_preference is True:

            print(
                "Setting relocation: Yes"
            )

            relocation_control = require_application_control(
                page,
                "If you do not live within a reasonable commute from the stated office location, are you willing to relocate?",
            )

            select_greenhouse_option(
                page,
                get_control_id(
                    relocation_control
                ),
                "Yes",
            )

            handled_question_ids.add(
                get_control_id(
                    relocation_control
                )
            )

        print()
        print(
            "Processing application questions..."
        )

        results = process_application_questions(
            page,
            profile,
            handled_question_ids=handled_question_ids,
        )

        print_question_results(
            results
        )

        # -------------------------------------------------
        # Browser-state verification
        # -------------------------------------------------

        verification = verify_application_state(
            page,
            profile,
            results["handled_questions"],
        )

        print()
        print("=" * 80)
        print(
            "AUTOFILL COMPLETE"
        )
        print("=" * 80)

        print()

        if results[
            "skipped_questions"
        ]:

            print(
                "WARNING: Some questions were "
                "skipped."
            )

            print(
                "Review the form carefully before "
                "submitting."
            )

        elif results[
            "unknown_required"
        ]:

            print(
                "WARNING: Required questions "
                "were detected."
            )

            print(
                "Review the form carefully before "
                "submitting."
            )

        elif not verification[
            "passed"
        ]:

            print(
                "WARNING: Browser-state verification "
                "failed."
            )

            print(
                "Do NOT submit this application."
            )

        else:

            print(
                "All required questions were handled."
            )

            print(
                "Browser-state verification passed."
            )

        print()

        print(
            "The application has NOT been submitted."
        )

        print(
            "JobAgent will NOT click "
            "'Submit application'."
        )

        print()

        if verification[
            "passed"
        ]:

            print(
                "SAFE STOP: Application is filled "
                "and verified, but submission remains "
                "a manual user action."
            )

        else:

            print(
                "SAFE STOP: Verification did not "
                "fully pass. Submission must remain "
                "blocked."
            )

        print()
        print("=" * 80)

        input(
            "Press Enter to close the browser..."
        )

        browser.close()


if __name__ == "__main__":
    main()