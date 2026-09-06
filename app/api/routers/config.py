"""Configuration endpoints for reading profile, sources, and answers."""
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from app.api.schemas.profile import ProfileSchema
from app.application.answers import load_answers
from app.application.prepare import load_answer_bank
from app.job_matcher import load_profile
from app.jobs.greenhouse import load_sources

router = APIRouter(prefix="/api/config", tags=["Configuration"])


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
