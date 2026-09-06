"""Configuration endpoints for reading and atomically updating profile, sources, and answers."""
import os
import json
import tempfile
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from app.api.schemas.profile import ProfileSchema
from app.application.answers import load_answers
from app.application.prepare import load_answer_bank
from app.job_matcher import load_profile, PROFILE_FILE
from app.jobs.greenhouse import load_sources

router = APIRouter(prefix="/api/config", tags=["Configuration"])


def atomic_write_json(file_path: Path, data: dict):
    """
    Atomically write data to a JSON file using a temp file + flush + fsync + replace.
    Ensures that data/profile.json is never left in a partially written or corrupt state.
    """
    file_path = file_path.resolve()
    parent = file_path.parent
    parent.mkdir(parents=True, exist_ok=True)

    # Use same directory to guarantee atomic rename across the filesystem
    fd, tmp_file = tempfile.mkstemp(prefix="profile_tmp_", suffix=".json", dir=str(parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        # Atomically replace target file
        os.replace(tmp_file, file_path)
    except Exception:
        if os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except Exception:
                pass
        raise


@router.get("/profile", response_model=ProfileSchema)
def get_user_profile():
    """Read the current profile from data/profile.json."""
    try:
        data = load_profile()
        return ProfileSchema(**data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load profile.json: {str(e)}",
        )


@router.put("/profile", response_model=ProfileSchema)
def update_user_profile(profile_data: ProfileSchema):
    """
    Atomically update data/profile.json with validated profile data.
    Preserves existing nested structures and ensures backward compatibility.
    """
    # 1. Validation checks
    if not profile_data.name.strip():
        raise HTTPException(status_code=422, detail="Candidate name cannot be empty.")
    if not profile_data.email.strip() or "@" not in profile_data.email:
        raise HTTPException(status_code=422, detail="A valid candidate email address is required.")
    if not profile_data.phone.strip():
        raise HTTPException(status_code=422, detail="Candidate phone number cannot be empty.")
    if not profile_data.location.strip():
        raise HTTPException(status_code=422, detail="Candidate location cannot be empty.")

    # 2. Read existing profile to preserve any unedited fields
    try:
        existing_profile = load_profile()
    except Exception:
        existing_profile = {}

    # 3. Prepare clean updated dictionary
    updated_dict = profile_data.model_dump(exclude_none=True)

    # Preserve projects from existing profile if not provided in update
    if "projects" not in updated_dict and "projects" in existing_profile:
        updated_dict["projects"] = existing_profile["projects"]

    # Preserve any other top-level keys that may exist in existing profile
    for key, val in existing_profile.items():
        if key not in updated_dict:
            updated_dict[key] = val

    # 4. Write atomically
    try:
        atomic_write_json(PROFILE_FILE, updated_dict)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to atomically write profile.json: {str(e)}",
        )

    # 5. Return persisted profile
    return ProfileSchema(**updated_dict)


@router.get("/sources", response_model=Dict[str, Any])
def get_sources_list():
    """Read configured job sources from data/sources.json."""
    try:
        return load_sources()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load sources.json: {str(e)}",
        )


@router.get("/answers", response_model=Dict[str, Any])
def get_answers():
    """Read answers from data/answers.json and candidate bank from data/application_answers.json."""
    answers = load_answers()
    try:
        application_answers = load_answer_bank()
    except Exception:
        application_answers = {}

    return {
        "answers": answers,
        "application_answers": application_answers,
    }
