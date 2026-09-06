import json
import re
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


def try_fill_application_answer(
    page,
    control,
    answer,
):
    """Safely fill a standard or common Greenhouse custom control."""

    answer = str(answer).strip()
    if not answer:
        return False

    field_type = get_field_type(control)
    normalized_answer = normalize_question_text(answer)
    custom = is_custom_control(control)

    # Normal text-like controls. A readonly/custom Greenhouse text input
    # must not be treated as an ordinary text field.
    if is_safe_for_saved_text_answer(control) and not custom:
        control.fill(answer)
        return True

    # Native select.
    if field_type == "select":
        for kwargs in (
            {"label": answer},
            {"value": answer},
        ):
            try:
                control.select_option(**kwargs)
                return True
            except Exception:
                pass

    # Checkbox controls.
    if field_type == "checkbox":
        if normalized_answer in {"yes", "true", "1"}:
            control.check()
            return True
        if normalized_answer in {"no", "false", "0"}:
            control.uncheck()
            return True

    # Radio buttons and labelled custom controls.
    if field_type == "radio":
        field_id = control.get_attribute("id") or ""

        if field_id:
            label = page.locator(
                f'label[for="{field_id}"]'
            )
            if label.count() > 0:
                text = normalize_question_text(label.first.inner_text())
                if text == normalized_answer or normalized_answer in text:
                    label.first.click()
                    return True

        aria_label = normalize_question_text(
            control.get_attribute("aria-label") or ""
        )
        if aria_label == normalized_answer or normalized_answer in aria_label:
            control.click()
            return True

        try:
            parent = control.locator("xpath=..")
            parent_text = normalize_question_text(parent.inner_text())
            if normalized_answer in parent_text:
                option = parent.get_by_text(
                    re.compile(
                        rf"^\s*{re.escape(answer)}\s*$",
                        re.IGNORECASE,
                    )
                ).last
                if option.count() > 0:
                    option.click()
                    return True
        except Exception:
            pass

    # Greenhouse custom combobox/listbox.
    role = (
        control.get_attribute("role") or ""
    ).lower()

    if role in {"combobox", "listbox"} or control.get_attribute("aria-haspopup"):
        control.click()
        page.wait_for_timeout(300)

        option = page.locator(
            '[role="option"]'
        ).filter(
            has_text=answer
        ).last

        if option.count() > 0:
            option.click()
            page.wait_for_timeout(300)
            return True

    # Greenhouse sometimes exposes a readonly text input with a nearby
    # button instead of a role=combobox. Treat it as a custom select.
    if control.get_attribute("readonly") is not None:
        try:
            control.click()
            page.wait_for_timeout(300)

            option = page.locator(
                '[role="option"]'
            ).filter(
                has_text=answer
            ).last

            if option.count() > 0:
                option.click()
                page.wait_for_timeout(300)
                return True
        except Exception:
            pass

    return False


def handle_profile_link_fields(
    page,
    profile,
    handled_question_ids,
):
    """Handle LinkedIn/GitHub/portfolio fields by their rendered labels.

    The labels and field IDs vary between Greenhouse forms, so this uses
    question text rather than employer-specific IDs.
    """

    handled = []
    controls = page.locator(
        'input, textarea, select, [role="combobox"], '
        '[role="listbox"], [role="radio"], [role="switch"]'
    )

    values = {
        "linkedin": profile.get("linkedin", ""),
        "github": profile.get("github", ""),
        "portfolio": profile.get("portfolio", ""),
    }

    for i in range(controls.count()):
        control = controls.nth(i)

        try:
            if not control.is_visible():
                continue

            field_id = control.get_attribute("id")
            field_type = get_field_type(control)

            if (
                not field_id
                or field_id in handled_question_ids
                or is_non_question_control(field_id, field_type)
            ):
                continue

            question = get_question_label(page, control)
            normalized = normalize_question_text(question)

            answer = None
            label = None

            if "github" in normalized and "linkedin" in normalized:
                answer = (
                    f"GitHub: {values['github']}\n"
                    f"LinkedIn: {values['linkedin']}"
                )
                label = "GitHub / LinkedIn"
            elif "linkedin" in normalized and values["linkedin"]:
                answer = values["linkedin"]
                label = "LinkedIn"
            elif "github" in normalized and values["github"]:
                answer = values["github"]
                label = "GitHub"
            elif (
                values["portfolio"]
                and any(
                    term in normalized
                    for term in (
                        "portfolio",
                        "personal website",
                        "personal site",
                        "website",
                    )
                )
            ):
                answer = values["portfolio"]
                label = "Portfolio / Website"

            if answer is None:
                continue

            if try_fill_application_answer(
                page,
                control,
                answer,
            ):
                handled_question_ids.add(field_id)
                handled.append(
                    {
                        "id": field_id,
                        "question": question,
                        "expected": answer,
                        "label": label,
                    }
                )
                print(f"Filled {label}: {question}")

        except Exception as error:
            print(
                f"Could not process profile field: {error}"
            )

    return handled


def process_application_questions(
    page,
    profile,
    handled_question_ids=None,
):
    """Process remaining application questions dynamically.

    Flow:
    1. Explicitly handled profile fields are skipped.
    2. Saved/profile answers are filled when safe.
    3. Common Greenhouse custom controls are handled when the answer is
       an explicit profile answer such as Yes/No.
    4. Unknown required text questions are shown to the user.
    5. Unknown required custom controls cause a SAFE STOP.
    6. Optional unknown questions are left untouched.
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

    for i in range(controls.count()):
        control = controls.nth(i)

        try:
            if not control.is_visible():
                continue

            field_id = control.get_attribute("id")
            if not field_id:
                continue

            field_type = get_field_type(control)
            custom = is_custom_control(control)

            if is_non_question_control(field_id, field_type):
                continue

            question = get_question_label(page, control)
            required = get_control_required_state(control)

            if field_id in known_question_ids:
                if field_id.startswith("question_"):
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

            resolution = resolve_question(question)
            answer = resolution.answer
            answer_source = resolution.source

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
                    print("SAFE PROFILE ANSWER FOUND:")
                    print(f"Question: {question}")
                    print(f"Answer: {answer}")
                    print("Source: explicit profile facts")

                try:
                    filled = try_fill_application_answer(
                        page,
                        control,
                        answer,
                    )
                except Exception as error:
                    filled = False
                    print(
                        f"Could not automatically fill {field_id}: {error}"
                    )

                if filled:
                    filled_answers.append(
                        {
                            "id": field_id,
                            "question": question,
                            "answer": answer,
                            "source": answer_source,
                        }
                    )

                    if answer_source == "profile":
                        save_answer(question, answer)

                    if field_id.startswith("question_"):
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

                if required:
                    unknown_required.append(
                        {
                            "id": field_id,
                            "question": question,
                            "type": field_type,
                            "custom": custom,
                        }
                    )

                continue

            if not required:
                continue

            # No interactive fallback is allowed here. The only user prompt
            # in this version is the dedicated internship availability selector.
            print()
            print("UNKNOWN REQUIRED CUSTOM CONTROL")
            print(f"Field: {field_id}")
            print(f"Question: {question}")
            print(f"Type: {field_type}")
            print("JobAgent will not guess how to interact with this control.")

            unknown_required.append(
                {
                    "id": field_id,
                    "question": question,
                    "type": field_type,
                    "custom": custom,
                }
            )

        except Exception as error:
            print(
                f"Could not inspect application control: {error}"
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

    For custom React Select / Greenhouse controls, extracts the selected option text
    from .select__single-value or [class*="singleValue"] / [class*="single-value"].
    For normal inputs/textareas this returns the input value.
    """

    try:
        single_val = control.evaluate(
            """
            e => {
                const container = e.closest('.select__control, .select-shell, [class*="control"]') || e.parentElement;
                if (!container) return null;
                const sv = container.querySelector('.select__single-value, [class*="singleValue"], [class*="single-value"]');
                return sv ? (sv.innerText || '').trim() : null;
            }
            """
        )
        if single_val:
            return single_val
    except Exception:
        pass

    try:
        value = control.input_value(
            timeout=2000
        )
        if value is not None and value.strip():
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
            if value and value.strip():
                return value.strip()
        except Exception:
            pass

    try:
        text = control.inner_text(
            timeout=2000
        )
        if text and text.strip():
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


def _greenhouse_selected_text(page, control):
    """Read the visible selected value from a Greenhouse custom control.

    Greenhouse often keeps the real input's value empty and renders the
    selected choice in an adjacent React element. Verification checks ARIA-selected options,
    .select__single-value elements, and the control's nearby rendered text.
    """
    texts = []

    try:
        single_val = control.evaluate("""
            e => {
                const container = e.closest('.select__control, .select-shell, [class*="control"]') || e.parentElement;
                if (!container) return null;
                const sv = container.querySelector('.select__single-value, [class*="singleValue"], [class*="single-value"]');
                return sv ? (sv.innerText || '').trim() : null;
            }
        """)
        if single_val:
            texts.append(single_val)
    except Exception:
        pass

    try:
        aria_value = control.get_attribute("aria-valuetext")
        if aria_value and aria_value.strip():
            texts.append(aria_value.strip())
    except Exception:
        pass

    try:
        selected = page.locator('[role="option"][aria-selected="true"]')
        for i in range(selected.count()):
            item = selected.nth(i)
            if item.is_visible():
                text = item.inner_text().strip()
                if text:
                    texts.append(text)
    except Exception:
        pass

    # De-duplicate while preserving useful DOM order.
    result = []
    seen = set()
    for text in texts:
        normalized = normalize_question_text(text)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(text)
    return result


def _greenhouse_value_matches(actual_texts, expected):
    expected_normalized = normalize_question_text(expected)
    if not expected_normalized:
        return False

    for text in actual_texts:
        normalized = normalize_question_text(text)
        if normalized == expected_normalized:
            return True
        # For long descriptive Yes/No answers, the rendered selected label
        # may contain the complete expected answer plus minor UI text.
        if len(expected_normalized) > 15 and expected_normalized in normalized:
            return True
        # School/degree/discipline/month selections can have minor prefixes.
        if expected_normalized in normalized and len(expected_normalized) > 3:
            return True
    return False


def verify_required_question_state(page, handled_questions):
    """Verify required controls using their actual Greenhouse selected state."""
    verification = []

    internship_ids = {
        str(item.get("id"))
        for item in handled_questions
        if "question_67942590" in str(item.get("id", "")) or item.get("group") == "internship_availability"
    }
    selected_internship_ids = {
        str(item.get("id"))
        for item in handled_questions
        if item.get("expected_option")
    }

    for item in handled_questions:
        if not item.get("required"):
            continue

        field_id = item.get("id")
        question = item.get("question", field_id)

        # Internship availability is one required choice group, not four
        # independently required checkboxes. Verify only the option the user
        # selected and ignore its unselected siblings.
        if str(field_id) in internship_ids and str(field_id) not in selected_internship_ids:
            continue

        safe_field_id = (
            str(field_id)
            .replace("\\", "\\\\")
            .replace('"', '\\"')
        )
        control = page.locator(f'[id="{safe_field_id}"]')

        if control.count() == 0:
            verification.append({
                "label": question,
                "field": field_id,
                "status": "FAIL",
                "expected": "required control present",
                "actual": "",
                "reason": "Required control not found",
            })
            continue

        field_type = get_field_type(control)
        role = (control.get_attribute("role") or "").lower()

        if field_type in {"checkbox", "radio"}:
            try:
                selected = control.is_checked()
            except Exception:
                selected = False
            if not selected:
                selected = control.get_attribute("aria-checked") == "true"

            verification.append({
                "label": question,
                "field": field_id,
                "status": "PASS" if selected else "FAIL",
                "expected": item.get("expected_option", "selected required control"),
                "actual": "selected" if selected else "not selected",
                "reason": "" if selected else "Required option is not selected",
            })
            continue

        if role in {"radio", "switch"}:
            selected = control.get_attribute("aria-checked") == "true"
            verification.append({
                "label": question,
                "field": field_id,
                "status": "PASS" if selected else "FAIL",
                "expected": item.get("expected_value", "selected required control"),
                "actual": "selected" if selected else "not selected",
                "reason": "" if selected else "Required option is not selected",
            })
            continue

        if field_id == "candidate-location":
            try:
                parent_text = control.evaluate(
                    "element => (element.parentElement && element.parentElement.parentElement) ? element.parentElement.parentElement.innerText : ''"
                ) or ""
                selected_ok = (
                    control.get_attribute("aria-invalid") != "true"
                    and "jamshedpur" in parent_text.lower()
                )
            except Exception:
                selected_ok = False
            verification.append({
                "label": question,
                "field": field_id,
                "status": "PASS" if selected_ok else "FAIL",
                "expected": "Jamshedpur location selected",
                "actual": "Jamshedpur suggestion selected" if selected_ok else "Location selection could not be verified",
                "reason": "" if selected_ok else "Greenhouse location autocomplete state is not verified",
            })
            continue

        expected_value = item.get("expected_value")
        actual = get_control_value(control)
        selected_texts = _greenhouse_selected_text(page, control)

        if expected_value:
            passed = _greenhouse_value_matches(
                [actual] + selected_texts,
                expected_value,
            )
            actual_display = actual or (selected_texts[0] if selected_texts else "")
            verification.append({
                "label": question,
                "field": field_id,
                "status": "PASS" if passed else "FAIL",
                "expected": expected_value,
                "actual": actual_display,
                "reason": "" if passed else "Selected Greenhouse value could not be verified",
            })
            continue

        if actual or selected_texts:
            verification.append({
                "label": question,
                "field": field_id,
                "status": "PASS",
                "expected": "non-empty required control",
                "actual": actual or (selected_texts[0] if selected_texts else ""),
                "reason": "",
            })
        else:
            verification.append({
                "label": question,
                "field": field_id,
                "status": "FAIL",
                "expected": "non-empty required control",
                "actual": "",
                "reason": "Required control appears empty",
            })

    return verification


def verify_application_state(
    page,
    profile,
    handled_questions,
    profile_fields=None,
):
    """Read-only verification of the browser state."""

    verification = []

    print()
    print("=" * 80)
    print("APPLICATION STATE VERIFICATION")
    print("=" * 80)

    first_name = profile["name"].split()[0]
    last_name = " ".join(profile["name"].split()[1:])

    # These are true standard Greenhouse profile fields. Optional fields
    # are only verified when they actually exist on the current form.
    for field_id, expected, label in (
        ("first_name", first_name, "First Name"),
        ("last_name", last_name, "Last Name"),
        ("email", profile["email"], "Email"),
        ("phone", profile["phone"], "Phone"),
    ):
        verification.append(
            verify_text_control(
                page,
                field_id,
                expected,
                label,
            )
        )

    preferred = page.locator("#preferred_name")
    if preferred.count() > 0 and preferred.is_visible():
        verification.append(
            verify_text_control(
                page,
                "preferred_name",
                first_name,
                "Preferred First Name",
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

    # Verify dynamically detected profile fields instead of relying on
    # employer-specific question IDs.
    for item in profile_fields or []:
        profile_field_id = str(item["id"])
        safe_profile_field_id = (
            profile_field_id
            .replace("\\", "\\\\")
            .replace('"', '\\\"')
        )
        control = page.locator(f'[id="{safe_profile_field_id}"]')

        if control.count() == 0:
            verification.append(
                {
                    "label": item["label"],
                    "field": item["id"],
                    "status": "FAIL",
                    "expected": item["expected"],
                    "actual": "",
                    "reason": "Control not found",
                }
            )
            continue

        actual = get_control_value(control)
        expected = str(item["expected"]).strip()
        normalized_actual = normalize_question_text(actual)

        if item.get("label") == "GitHub / LinkedIn":
            passed = (
                normalize_question_text(profile.get("github", "")) in normalized_actual
                and normalize_question_text(profile.get("linkedin", "")) in normalized_actual
            )
        else:
            passed = normalize_question_text(expected) == normalized_actual

        verification.append(
            {
                "label": item["label"],
                "field": item["id"],
                "status": "PASS" if passed else "FAIL",
                "expected": expected,
                "actual": actual,
                "reason": "" if passed else "Browser value does not match expected value",
            }
        )

    verification.extend(
        verify_required_question_state(
            page,
            handled_questions,
        )
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

        print(f"[{marker}] {item['label']}")

        if item.get("expected"):
            print(f"  Expected: {item['expected']}")
        if item.get("actual"):
            print(f"  Actual:   {item['actual']}")
        if item.get("reason"):
            print(f"  Reason:   {item['reason']}")
        print()

    print(f"Verification checks passed: {passed}")
    print(f"Verification checks failed: {failed}")

    verification_passed = failed == 0

    if verification_passed:
        print()
        print("APPLICATION STATE VERIFICATION: PASSED")
        print("All verified fields contain the expected values.")
    else:
        print()
        print("APPLICATION STATE VERIFICATION: FAILED")
        print("The application must be reviewed before submission.")

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



# ---------------------------------------------------------------------------
# JobAgent deterministic Greenhouse field handlers
# ---------------------------------------------------------------------------

VERIFIED_WORK_AUTHORIZATION = "Yes, I am currently eligible to work in the country where this role is based."
VERIFIED_VISA_SPONSORSHIP = "No, I do not require visa sponsorship now or in the future to continue working in the country where this role is based."
VERIFIED_WHATSAPP = "Yes"
VERIFIED_ACTIVE_OFFER = "I do not hold any active offer"
VERIFIED_SCHOOL = "RVS College Of Engineering And Technology, Jamshedpur"

INTERNSHIP_OPTIONS = [
    "January to June (6 months)",
    "May to July (10 weeks)",
    "June to August (10 weeks)",
    "None of these options work for me",
]


def _normalized_contains(text, *terms):
    normalized = normalize_question_text(text)
    return all(normalize_question_text(term) in normalized for term in terms)


def _visible_controls(page):
    controls = page.locator(
        'input, textarea, select, button, '
        '[role="combobox"], [role="listbox"], '
        '[role="radio"], [role="switch"]'
    )
    for index in range(controls.count()):
        control = controls.nth(index)
        try:
            if control.is_visible():
                yield control
        except Exception:
            continue


def _find_question_control(page, include_terms, exclude_terms=(), prefer_custom=True):
    matches = []
    for control in _visible_controls(page):
        try:
            field_id = control.get_attribute("id") or ""
            field_type = get_field_type(control)
            if not field_id or is_non_question_control(field_id, field_type):
                continue
            question = get_question_label(page, control)
            normalized = normalize_question_text(question)
            if all(normalize_question_text(term) in normalized for term in include_terms) and not any(
                normalize_question_text(term) in normalized for term in exclude_terms
            ):
                matches.append((control, question, field_type))
        except Exception:
            continue

    if not matches:
        return None

    if prefer_custom:
        for item in matches:
            if is_custom_control(item[0]):
                return item

    return matches[0]


def _option_text_matches(text, candidates):
    """Match Greenhouse dropdown options safely.

    Never use substring matching for short answers such as "No" or "Other":
    words such as "now" or "brothers" would otherwise cause false matches.
    Prefer exact text, then allow a longer candidate to match a descriptive
    option that starts with that candidate.
    """
    normalized = normalize_question_text(text)

    # Exact match always wins.
    for candidate in candidates:
        candidate_normalized = normalize_question_text(candidate)
        if normalized == candidate_normalized:
            return True

    # For descriptive candidates, allow the rendered option to contain the
    # candidate as a complete prefix. Never do this for "yes"/"no"/"other"/"others".
    short_exact_only = {"yes", "no", "other", "others"}
    for candidate in candidates:
        candidate_normalized = normalize_question_text(candidate)
        if candidate_normalized in short_exact_only:
            continue
        if (
            candidate_normalized
            and (
                normalized.startswith(candidate_normalized + ",")
                or normalized.startswith(candidate_normalized + " ")
                or (len(candidate_normalized) >= 6 and candidate_normalized in normalized)
            )
        ):
            return True

    return False


def _click_greenhouse_option(page, control, candidates):
    """Open a Greenhouse custom dropdown and select one of the candidates."""
    candidates = [str(item).strip() for item in candidates if str(item).strip()]

    def visible_options():
        return page.locator(
            '[role="option"]:visible, '
            '.select__option:visible, '
            '[role="listbox"] [role="option"]:visible, '
            '[role="listbox"] li:visible, '
            '[role="listbox"] button:visible, '
            '[role="listbox"] [role="menuitem"]:visible, '
            '[data-option-index]:visible, '
            'li[aria-selected]:visible, '
            'div[aria-selected]:visible'
        )

    def try_visible_options():
        options = visible_options()
        for index in range(options.count()):
            option = options.nth(index)
            try:
                text = option.inner_text().strip()
                if text and _option_text_matches(text, candidates):
                    option.click()
                    page.wait_for_timeout(400)
                    return text
            except Exception:
                continue
        return None

    # Step 1: Ensure input is focused and menu opened
    try:
        control.click()
        page.wait_for_timeout(200)
    except Exception:
        try:
            field_id = control.get_attribute("id")
            if not field_id:
                return None
            safe_id = str(field_id).replace("\\", "\\\\").replace('"', '\\"')
            page.locator(f'[id="{safe_id}"]').click(force=True)
        except Exception:
            return None

    # Check if a matching option is already visible (e.g. without typing)
    selected = try_visible_options()
    if selected is not None:
        return selected

    # Step 2: Try candidates by typing into the open combobox
    for candidate in candidates:
        try:
            control.press("Control+A")
            control.press("Backspace")
        except Exception:
            pass

        try:
            control.type(candidate, delay=30)
        except Exception:
            try:
                page.keyboard.type(candidate, delay=30)
            except Exception:
                try:
                    control.fill(candidate)
                except Exception:
                    continue

        # Wait for async Greenhouse API response (e.g. boards.greenhouse.io/v1/.../schools?term=...)
        page.wait_for_timeout(1200)

        selected = try_visible_options()
        if selected is not None:
            return selected

        # Some Greenhouse menus expose only visible text, not role=option.
        try:
            exact = page.get_by_text(
                re.compile(rf'^\s*{re.escape(candidate)}\s*$', re.IGNORECASE)
            )
            for index in range(exact.count() - 1, -1, -1):
                node = exact.nth(index)
                if node.is_visible():
                    text = node.inner_text().strip()
                    node.click()
                    page.wait_for_timeout(400)
                    return text
        except Exception:
            pass

    # If no candidate matched, press Escape to close the menu cleanly
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(150)
    except Exception:
        pass

    return None

def _select_field_option(page, include_terms, candidates, exclude_terms=(), label=None):
    found = _find_question_control(page, include_terms, exclude_terms)
    if not found:
        raise RuntimeError(
            f"Could not find Greenhouse field for {label or ' / '.join(include_terms)}"
        )

    control, question, _ = found
    selected = _click_greenhouse_option(page, control, candidates)
    if selected is None:
        # Native select fallback.
        try:
            for candidate in candidates:
                try:
                    control.select_option(label=candidate)
                    selected = candidate
                    break
                except Exception:
                    pass
        except Exception:
            pass

    if selected is None:
        raise RuntimeError(
            f"Could not select {candidates!r} for {question}"
        )

    print(f"Filled {label or question}: {selected}")
    return control, question, selected


def _fill_text_question(page, include_terms, answer, exclude_terms=(), label=None):
    found = _find_question_control(
        page,
        include_terms,
        exclude_terms=exclude_terms,
        prefer_custom=False,
    )
    if not found:
        raise RuntimeError(
            f"Could not find text field for {label or ' / '.join(include_terms)}"
        )

    control, question, _ = found
    try:
        control.fill(answer)
    except Exception:
        field_id = control.get_attribute("id")
        if not field_id:
            raise
        page.locator(f'#{field_id}').fill(answer)

    print(f"Filled {label or question}: {answer}")
    return control, question


def _find_school_fallback(page):
    for control in _visible_controls(page):
        try:
            field_id = control.get_attribute("id") or ""
            field_type = get_field_type(control)
            if not field_id or field_type not in {"text", "search", "textarea"}:
                continue
            question = normalize_question_text(get_question_label(page, control))
            aria = normalize_question_text(control.get_attribute("aria-label") or "")
            placeholder = normalize_question_text(control.get_attribute("placeholder") or "")
            combined = f"{question} {aria} {placeholder}"
            if "school name" in combined:
                return control, question
        except Exception:
            continue
    return None



def handle_candidate_location(page, profile, handled_question_ids):
    """Select the real Greenhouse autocomplete suggestion for current city."""
    field = page.locator("#candidate-location").first
    if field.count() == 0 or not field.is_visible():
        raise RuntimeError("Could not find the Greenhouse candidate location field.")

    location = profile.get("location", "Jamshedpur, India")
    field.fill(location)
    page.wait_for_timeout(1200)

    options = page.locator('[role="option"]:visible')
    selected_text = None
    for index in range(options.count()):
        option = options.nth(index)
        try:
            text = option.inner_text().strip()
            if "jamshedpur" in text.lower():
                option.click()
                page.wait_for_timeout(500)
                selected_text = text
                break
        except Exception:
            continue

    if selected_text is None:
        # Retry with the city + state wording used by Greenhouse.
        field.fill("")
        page.wait_for_timeout(200)
        field.fill("Jamshedpur, Jharkhand")
        page.wait_for_timeout(1200)
        options = page.locator('[role="option"]:visible')
        for index in range(options.count()):
            option = options.nth(index)
            try:
                text = option.inner_text().strip()
                if "jamshedpur" in text.lower():
                    option.click()
                    page.wait_for_timeout(500)
                    selected_text = text
                    break
            except Exception:
                continue

    if selected_text is None:
        raise RuntimeError("Could not select Jamshedpur from the Greenhouse location suggestions.")

    handled_question_ids.add("candidate-location")
    print(f"Filled Location (City): {selected_text}")
    return [{
        "id": "candidate-location",
        "question": "Location (City)",
        "type": "text",
        "custom": True,
        "required": True,
        "expected_location": "Jamshedpur",
    }]

def handle_education_fields(page, handled_question_ids):
    """Fill the known education fields deterministically."""
    handled = []

    # School: select RVS when present; otherwise choose Other and fill the
    # dedicated free-text school-name field.
    school = _find_question_control(page, ("school",), exclude_terms=("school name",))
    if not school:
        raise RuntimeError("Could not find the primary School field.")

    school_control, school_question, _ = school
    selected = _click_greenhouse_option(
        page,
        school_control,
        [VERIFIED_SCHOOL],
    )

    if selected is None:
        # If RVS is not present, explicitly try the Greenhouse "Other"
        # option before using the dedicated school-name fallback.
        selected = _click_greenhouse_option(
            page,
            school_control,
            ["Other", "Others"],
        )

    if selected is None:
        # The primary School dropdown is mandatory. If RVS is not listed,
        # Greenhouse requires the explicit Other/Others choice before the
        # separate school-name fallback can be filled. Never silently bypass
        # that required dropdown selection.
        raise RuntimeError(
            "RVS College was not available and the mandatory Greenhouse Other/Others school option could not be selected."
        )

    # Selecting Other reveals/activates the dedicated school-name field.
    if normalize_question_text(selected) in {"other", "others"}:
        fallback = _find_school_fallback(page)
        if not fallback:
            page.wait_for_timeout(500)
            fallback = _find_school_fallback(page)

        if not fallback:
            raise RuntimeError(
                "Greenhouse School is set to Other, but the required school-name fallback field was not found."
            )

        fallback_control, fallback_question = fallback
        fallback_control.fill(VERIFIED_SCHOOL)
        page.wait_for_timeout(250)
        handled_question_ids.add(fallback_control.get_attribute("id"))
        handled.append({
            "id": fallback_control.get_attribute("id"),
            "question": fallback_question,
            "type": get_field_type(fallback_control),
            "custom": False,
            "required": get_control_required_state(fallback_control),
            "expected_value": VERIFIED_SCHOOL,
        })
        print(f"Filled fallback School name: {VERIFIED_SCHOOL}")

    school_expected = selected

    handled_question_ids.add(school_control.get_attribute("id"))
    handled.append({
        "id": school_control.get_attribute("id"),
        "question": school_question,
        "type": get_field_type(school_control),
        "custom": True,
        "required": get_control_required_state(school_control),
        "expected_value": (
            selected if selected is not None else "Other"
        ),
    })
    print(f"Filled School: {school_expected}")

    degree_control, degree_question, degree_selected = _select_field_option(
        page,
        ("degree",),
        ["Bachelor's Degree", "Bachelor's degree", "Bachelor Degree", "Bachelor"],
        label="Degree",
    )
    handled_question_ids.add(degree_control.get_attribute("id"))
    handled.append({
        "id": degree_control.get_attribute("id"),
        "question": degree_question,
        "type": get_field_type(degree_control),
        "custom": True,
        "required": get_control_required_state(degree_control),
        "expected_value": degree_selected or "Bachelor's Degree",
    })

    discipline_control, discipline_question, discipline_selected = _select_field_option(
        page,
        ("discipline",),
        ["Computer Science", "Computer Science and Engineering", "Computer Science & Engineering"],
        label="Discipline",
    )
    handled_question_ids.add(discipline_control.get_attribute("id"))
    handled.append({
        "id": discipline_control.get_attribute("id"),
        "question": discipline_question,
        "type": get_field_type(discipline_control),
        "custom": True,
        "required": get_control_required_state(discipline_control),
        "expected_value": discipline_selected or "Computer Science",
    })

    start_found = _find_question_control(
        page,
        ("start", "year"),
        prefer_custom=False,
    )
    if not start_found:
        raise RuntimeError("Could not find Greenhouse field for Education start year")
    start_control, start_question, _ = start_found
    start_control.fill("2020")
    page.wait_for_timeout(150)
    print("Filled Education start year: 2020")
    handled_question_ids.add(start_control.get_attribute("id"))
    handled.append({
        "id": start_control.get_attribute("id"),
        "question": start_question,
        "type": get_field_type(start_control),
        "custom": True,
        "required": get_control_required_state(start_control),
    })

    end_month_control, end_month_question, end_month_selected = _select_field_option(
        page,
        ("end", "month"),
        ["August"],
        label="Education end month",
    )
    handled_question_ids.add(end_month_control.get_attribute("id"))
    handled.append({
        "id": end_month_control.get_attribute("id"),
        "question": end_month_question,
        "type": get_field_type(end_month_control),
        "custom": True,
        "required": get_control_required_state(end_month_control),
        "expected_value": end_month_selected or "August",
    })

    end_year_found = _find_question_control(
        page,
        ("end", "year"),
        prefer_custom=False,
    )
    if not end_year_found:
        raise RuntimeError("Could not find Greenhouse field for Education end year")
    end_year_control, end_year_question, _ = end_year_found
    end_year_control.fill("2023")
    page.wait_for_timeout(150)
    print("Filled Education end year: 2023")
    handled_question_ids.add(end_year_control.get_attribute("id"))
    handled.append({
        "id": end_year_control.get_attribute("id"),
        "question": end_year_question,
        "type": get_field_type(end_year_control),
        "custom": True,
        "required": get_control_required_state(end_year_control),
    })

    return handled


def _select_yes_no_question(page, include_terms, answer, label):
    found = _find_question_control(page, include_terms)
    if not found:
        raise RuntimeError(f"Could not find {label} field.")

    control, question, field_type = found
    answer_normalized = normalize_question_text(answer)

    # Try the associated custom dropdown first.
    # Use the exact requested option first.  For these Greenhouse controls
    # the visible option text is the source of truth; never infer No/Yes
    # from the surrounding question.
    if answer_normalized == "yes":
        option_candidates = [
            "Yes",
            "Yes, I am currently eligible to work in the country where this role is based.",
        ]
    else:
        option_candidates = [
            "No",
            "No, I do not require visa sponsorship now or in the future to continue working in the country where this role is based.",
        ]

    selected = _click_greenhouse_option(page, control, option_candidates)

    if selected is None:
        # Radio/checkbox fallback.  Do NOT search for the bare word
        # "yes"/"no" inside the question text: words such as "now" contain
        # "no" and can cause the first option (often Yes) to be selected.
        # Only accept a control when its rendered label is an actual option
        # label matching the requested answer.
        desired_option_prefixes = (
            ["yes", "yes,"] if answer_normalized == "yes"
            else ["no", "no,"]
        )

        for candidate in _visible_controls(page):
            try:
                field_id = candidate.get_attribute("id") or ""
                field_type2 = get_field_type(candidate)
                if (
                    field_type2 not in {"radio", "checkbox"}
                    and (candidate.get_attribute("role") or "").lower()
                    not in {"radio", "switch"}
                ):
                    continue

                candidate_text = normalize_question_text(
                    get_question_label(page, candidate)
                )

                # Match the option text itself, not merely a substring of
                # the surrounding question.
                option_match = (
                    candidate_text == answer_normalized
                    or candidate_text.startswith(tuple(desired_option_prefixes))
                    and (
                        candidate_text.startswith(answer_normalized + ",")
                        or candidate_text == answer_normalized
                    )
                )

                if not option_match:
                    # Also inspect the associated <label>, which is how
                    # several Greenhouse custom radio controls expose the
                    # actual option text.
                    label_text = ""
                    if field_id:
                        label = page.locator(
                            f'label[for="{field_id.replace(chr(92), chr(92)*2).replace(chr(34), chr(92)+chr(34))}"]'
                        )
                        if label.count() > 0:
                            label_text = normalize_question_text(
                                label.first.inner_text()
                            )

                    option_match = (
                        label_text == answer_normalized
                        or label_text.startswith(tuple(desired_option_prefixes))
                    )

                if not option_match:
                    continue

                if field_type2 in {"radio", "checkbox"}:
                    candidate.check()
                else:
                    candidate.click()

                selected = candidate_text or label_text
                break
            except Exception:
                continue

    if selected is None:
        raise RuntimeError(f"Could not select {answer!r} for {question}")

    print(f"Filled {label}: {selected}")
    return control, question, selected


def handle_verified_application_questions(page, handled_question_ids):
    """Fill the user's verified answers without asking for legal information."""
    handled = []

    active = _find_question_control(page, ("active offer",), prefer_custom=False)
    if active:
        control, question, _ = active
        control.fill(VERIFIED_ACTIVE_OFFER)
        handled_question_ids.add(control.get_attribute("id"))
        handled.append({
            "id": control.get_attribute("id"),
            "question": question,
            "type": get_field_type(control),
            "custom": False,
            "required": get_control_required_state(control),
            "expected_value": VERIFIED_ACTIVE_OFFER,
        })
        print(f"Filled Active offer deadline: {VERIFIED_ACTIVE_OFFER}")

    work_control, work_question, work_selected = _select_yes_no_question(
        page,
        ("eligible", "work"),
        "yes",
        "Work authorization",
    )
    handled_question_ids.add(work_control.get_attribute("id"))
    handled.append({
        "id": work_control.get_attribute("id"),
        "question": work_question,
        "type": get_field_type(work_control),
        "custom": True,
        "required": get_control_required_state(work_control),
        "expected_value": work_selected or VERIFIED_WORK_AUTHORIZATION,
    })

    visa_control, visa_question, visa_selected = _select_yes_no_question(
        page,
        ("visa", "sponsorship"),
        "no",
        "Visa sponsorship",
    )
    handled_question_ids.add(visa_control.get_attribute("id"))
    handled.append({
        "id": visa_control.get_attribute("id"),
        "question": visa_question,
        "type": get_field_type(visa_control),
        "custom": True,
        "required": get_control_required_state(visa_control),
        "expected_value": visa_selected or VERIFIED_VISA_SPONSORSHIP,
    })

    whatsapp_control, whatsapp_question, whatsapp_selected = _select_yes_no_question(
        page,
        ("whatsapp",),
        "yes",
        "WhatsApp recruiting messages",
    )
    handled_question_ids.add(whatsapp_control.get_attribute("id"))
    handled.append({
        "id": whatsapp_control.get_attribute("id"),
        "question": whatsapp_question,
        "type": get_field_type(whatsapp_control),
        "custom": True,
        "required": get_control_required_state(whatsapp_control),
        "expected_value": whatsapp_selected or VERIFIED_WHATSAPP,
    })

    return handled


def handle_internship_availability(page, handled_question_ids):
    """Ask only the internship cohort/date question and select exactly one option."""
    controls = page.locator('input[type="checkbox"]')
    option_controls = []

    for index in range(controls.count()):
        control = controls.nth(index)
        try:
            if not control.is_visible():
                continue
            question = get_question_label(page, control)
            normalized = normalize_question_text(question)
            matched = None
            for option in INTERNSHIP_OPTIONS:
                if normalize_question_text(option) in normalized:
                    matched = option
                    break
            if matched:
                option_controls.append((matched, control, question))
        except Exception:
            continue

    if not option_controls:
        raise RuntimeError("Could not find the internship availability options.")

    # Preserve page order and remove duplicate DOM controls.
    unique = []
    seen = set()
    for item in option_controls:
        if item[0] not in seen:
            unique.append(item)
            seen.add(item[0])

    print()
    print("=" * 80)
    print("INTERNSHIP AVAILABILITY REQUIRED")
    print("=" * 80)
    print("Choose your internship availability/cohort:")
    for index, option in enumerate(INTERNSHIP_OPTIONS, start=1):
        print(f"  {index}. {option}")

    while True:
        choice = input("Select 1-4: ").strip()
        try:
            selected_index = int(choice)
        except ValueError:
            print("Please enter 1, 2, 3, or 4.")
            continue
        if 1 <= selected_index <= 4:
            selected_option = INTERNSHIP_OPTIONS[selected_index - 1]
            break
        print("Please enter 1, 2, 3, or 4.")

    selected_control = None
    selected_question = None
    for option, control, question in unique:
        field_id = control.get_attribute("id")
        handled_question_ids.add(field_id)
        if option == selected_option:
            selected_control = control
            selected_question = question
        else:
            try:
                if control.is_checked():
                    control.uncheck()
            except Exception:
                pass

    if selected_control is None:
        raise RuntimeError(f"Internship option {selected_option!r} was not found on the form.")

    try:
        selected_control.check()
    except Exception:
        field_id = selected_control.get_attribute("id")
        label = page.locator(f'label[for="{field_id}"]') if field_id else None
        if label and label.count() > 0:
            label.first.click()
        else:
            selected_control.click()

    page.wait_for_timeout(250)
    print(f"Selected internship availability: {selected_option}")

    return [{
        "id": selected_control.get_attribute("id"),
        "question": selected_question,
        "type": "checkbox",
        "custom": True,
        "required": True,
        "group": "internship_availability",
        "expected_option": selected_option,
    }]


def handle_all_known_fields(page, profile, handled_question_ids):
    """Run every deterministic handler before the generic question scanner."""
    handled = []
    handled.extend(handle_candidate_location(page, profile, handled_question_ids))
    handled.extend(handle_education_fields(page, handled_question_ids))
    handled.extend(handle_verified_application_questions(page, handled_question_ids))
    handled.extend(handle_internship_availability(page, handled_question_ids))
    return handled

def main(package_path=None):
    profile = load_profile()

    if package_path is not None:
        package_path = Path(package_path)

        if not package_path.exists():
            raise FileNotFoundError(
                f"Application package not found: {package_path}"
            )

        with package_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            application = json.load(file)

        application_status = (
            application.get(
                "application",
                {},
            ).get("status")
        )

        if application_status != "ready_for_review":
            raise RuntimeError(
                "Application package is not "
                "ready_for_review."
            )

    else:
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

        # -------------------------------------------------
        # Locate Greenhouse application form
        # -------------------------------------------------

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

        greenhouse_frame = None

        for frame in page.frames:

            if (
                "job-boards.greenhouse.io/embed/job_app"
                in frame.url
            ):

                greenhouse_frame = frame

                break

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

                browser.close()

                return False

        else:

            form_page = greenhouse_frame

        print(
            "Greenhouse application form found."
        )

        form_page.wait_for_timeout(
            1500
        )

        print()
        print(
            "Filling personal information..."
        )

        form_page.locator(
            "#first_name"
        ).fill(
            first_name
        )

        form_page.locator(
            "#last_name"
        ).fill(
            last_name
        )

        preferred_name_control = form_page.locator(
            "#preferred_name"
        )

        if preferred_name_control.count() > 0:

            preferred_name_control.fill(
                first_name
            )

        else:

            print(
                "Preferred name field not present. Skipping."
            )

        form_page.locator(
            "#email"
        ).fill(
            profile["email"]
        )

        form_page.locator(
            "#phone"
        ).fill(
            profile["phone"]
        )

        print(
            "Setting country: India"
        )

        select_greenhouse_option(
            form_page,
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

        form_page.locator(
            "#resume"
        ).set_input_files(
            str(RESUME_PATH)
        )

        print(
            "Handling all known application fields..."
        )

        handled_question_ids = set()

        # Deterministic fields use verified profile facts. The only interactive
        # prompt is internship availability/cohort.
        known_field_results = handle_all_known_fields(
            form_page,
            profile,
            handled_question_ids,
        )

        print()
        print(
            "Handling dynamic profile fields..."
        )

        profile_fields = handle_profile_link_fields(
            form_page,
            profile,
            handled_question_ids,
        )

        print()
        print(
            "Processing remaining application questions..."
        )

        results = process_application_questions(
            form_page,
            profile,
            handled_question_ids=handled_question_ids,
        )

        all_handled = []
        seen_handled_ids = set()
        for item in known_field_results + results["handled_questions"]:
            item_id = str(item.get("id", ""))
            if item_id and item_id in seen_handled_ids:
                continue
            if item_id:
                seen_handled_ids.add(item_id)
            all_handled.append(item)
        results["handled_questions"] = all_handled

        print_question_results(
            results
        )

        # -------------------------------------------------
        # Browser-state verification
        # -------------------------------------------------

        verification = verify_application_state(
            form_page,
            profile,
            results["handled_questions"],
            profile_fields=profile_fields,
        )

        print()
        print("=" * 80)
        print("AUTOFILL COMPLETE")
        print("=" * 80)
        print()

        if results["skipped_questions"]:
            print("WARNING: Some questions were skipped.")
            print("Submission is BLOCKED.")

        elif results["unknown_required"]:
            print("WARNING: Unknown required questions remain.")
            print("Submission is BLOCKED.")

        elif not verification["passed"]:
            print("WARNING: Browser-state verification failed.")
            print("Submission is BLOCKED.")

        else:
            print("All required questions were handled.")
            print("Browser-state verification passed.")

        print()

        # -------------------------------------------------
        # Submission safety gate
        # -------------------------------------------------

        if (
            not verification["passed"]
            or results["skipped_questions"]
            or results["unknown_required"]
        ):
            print("=" * 80)
            print("SAFE STOP")
            print("=" * 80)
            print()
            print("JobAgent will NOT submit this application.")
            print()

            input(
                "Press Enter to close the browser..."
            )

            browser.close()
            return

        # -------------------------------------------------
        # Final human confirmation
        # -------------------------------------------------

        job = application.get(
            "job",
            {},
        )

        print("=" * 80)
        print("READY TO SUBMIT")
        print("=" * 80)
        print()

        print(
            f"Company: {job.get('company', 'Unknown')}"
        )

        print(
            f"Role: {job.get('title', 'Unknown')}"
        )

        print(
            f"Location: {job.get('location', 'Unknown')}"
        )

        print(
            f"Match score: {job.get('match_score', 'Unknown')}"
        )

        print(
            f"Application URL: {job.get('url', '')}"
        )

        print()
        print("Resume: verified")
        print("Required questions: handled")
        print("Browser verification: PASSED")
        print()

        print(
            "The application has NOT been submitted yet."
        )

        print(
            "Review the browser form before continuing."
        )

        print()

        confirmation = input(
            "Submit this application? [Y/N]: "
        ).strip().lower()

        if confirmation not in {"y", "yes"}:
            print()
            print("SUBMISSION CANCELLED.")
            print("The application has NOT been submitted.")
            print()

            input(
                "Press Enter to close the browser..."
            )

            browser.close()
            return False

        # -------------------------------------------------
        # Submit
        # -------------------------------------------------

        print()
        print("=" * 80)
        print("SUBMITTING APPLICATION")
        print("=" * 80)
        print()

        submit_button = form_page.get_by_role(
            "button",
            name=re.compile(
                r"^\s*submit application\s*$",
                re.IGNORECASE,
            ),
        )

        if not submit_button.is_visible():
            print(
                "SUBMISSION BLOCKED: "
                "'Submit application' button was not visible."
            )

            input(
                "Press Enter to close the browser..."
            )

            browser.close()
            return False

        if not submit_button.is_enabled():
            print(
                "SUBMISSION BLOCKED: "
                "'Submit application' button is disabled."
            )

            input(
                "Press Enter to close the browser..."
            )

            browser.close()
            return False

        print(
            "Submit button found and enabled."
        )

        print(
            "Clicking submit..."
        )

        submit_button.click()

        # -------------------------------------------------
        # Submission result verification
        # -------------------------------------------------

        print(
            "Waiting for the application response..."
        )

        page.wait_for_timeout(3000)

        current_url = page.url

        body_text = page.locator(
            "body"
        ).inner_text().lower()

        success_patterns = [
            "thank you",
            "application submitted",
            "application has been submitted",
            "successfully submitted",
            "your application has been received",
        ]

        success_detected = any(
            pattern in body_text
            for pattern in success_patterns
        )

        if success_detected:
            print()
            print("=" * 80)
            print("APPLICATION SUBMITTED")
            print("=" * 80)
            print()
            print(
                "JobAgent detected a successful "
                "submission confirmation."
            )
            print(
                f"Final URL: {current_url}"
            )

            browser.close()
            return True

        else:
            print()
            print("=" * 80)
            print("SUBMISSION RESULT UNCERTAIN")
            print("=" * 80)
            print()
            print(
                "The submit button was clicked, but "
                "JobAgent could not verify a success "
                "confirmation."
            )
            print(
                f"Current URL: {current_url}"
            )

            browser.close()
            return False
            print()
            print(
                "DO NOT automatically retry submission."
            )
            print(
                "Review the browser manually."
            )

        print()
        print("=" * 80)

        input(
            "Press Enter to close the browser..."
        )

        browser.close()


if __name__ == "__main__":
    main()
