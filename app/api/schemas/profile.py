"""Profile schema with strict validation and preservation of existing fields."""
from typing import Optional, Any, Dict, List, Union
from pydantic import BaseModel, ConfigDict, Field


class EducationItem(BaseModel):
    degree: str = Field(..., min_length=1)
    institution: str = Field(..., min_length=1)
    start: Optional[str] = None
    end: Optional[str] = None
    graduation: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class ExperienceItem(BaseModel):
    company: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    start: Optional[str] = None
    end: Optional[str] = None
    achievements: Optional[List[str]] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class ApplicationPreferences(BaseModel):
    okay_with_five_day_office: Optional[bool] = True
    willing_to_relocate: Optional[bool] = True

    model_config = ConfigDict(extra="allow")


class ProfileSchema(BaseModel):
    name: str = Field(..., min_length=1, description="Candidate full name")
    email: str = Field(..., min_length=3, description="Candidate email address")
    phone: str = Field(..., min_length=3, description="Candidate phone number")
    location: str = Field(..., min_length=1, description="Candidate current location")
    target_roles: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    years_of_experience: Union[int, float] = 0
    education: List[Dict[str, Any]] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)
    remote_preference: str = ""
    minimum_salary: str = ""
    notice_period: str = ""
    work_authorization: str = ""
    application_preferences: Optional[Dict[str, Any]] = None
    summary: str = ""
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    projects: Optional[List[Dict[str, Any]]] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None

    model_config = ConfigDict(extra="allow")
