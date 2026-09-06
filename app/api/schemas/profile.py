"""Profile schema with strict preservation of existing fields."""
from typing import Optional, Any, Dict, List, Union
from pydantic import BaseModel, ConfigDict, Field


class EducationItem(BaseModel):
    degree: str
    institution: str
    start: Optional[str] = None
    end: Optional[str] = None
    graduation: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class ExperienceItem(BaseModel):
    company: str
    role: str
    start: Optional[str] = None
    end: Optional[str] = None
    achievements: Optional[List[str]] = None
    model_config = ConfigDict(extra="allow")


class ProfileSchema(BaseModel):
    name: str
    email: str
    phone: str
    location: str
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
    links: Optional[Dict[str, Any]] = None
    projects: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(extra="allow")
