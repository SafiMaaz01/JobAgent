from pathlib import Path
import json


PROFILE_FILE = Path("data/profile.json")


def create_profile():
    profile = {
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "target_roles": [],
        "skills": [],
        "years_of_experience": 0,
        "education": [],
        "preferred_locations": [],
        "remote_preference": "",
        "minimum_salary": "",
        "notice_period": "",
        "work_authorization": "",
        "summary": "",
        "experience": []
    }

    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    print(f"Profile created at: {PROFILE_FILE}")


if __name__ == "__main__":
    create_profile()