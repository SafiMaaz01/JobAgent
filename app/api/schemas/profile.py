"""Profile schema with strict validation and preservation of existing fields.

This schema validates candidate information stored in data/profile.json.
It supports deep nesting (education, experience, target roles, application preferences)
and ensures that all candidate attributes are correctly formatted before being saved.
Extra fields are permitted to avoid dropping any user-defined configuration.
"""
from typing import Optional, Any, Dict, List, Union
from pydantic import BaseModel, ConfigDict, Field


class EducationItem(BaseModel):
    """Represents an academic degree or educational credential."""
    degree: str = Field(..., min_length=1, description="Degree or program title")
    institution: str = Field(..., min_length=1, description="University or institution name")
    start: Optional[str] = None
    end: Optional[str] = None
    graduation: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class ExperienceItem(BaseModel):
    """Represents a previous employment role and key accomplishments."""
    company: str = Field(..., min_length=1, description="Employer company name")
    role: str = Field(..., min_length=1, description="Job title held")
    start: Optional[str] = None
    end: Optional[str] = None
    achievements: Optional[List[str]] = Field(default_factory=list, description="Bullet points of impact")

    model_config = ConfigDict(extra="allow")


class ApplicationPreferences(BaseModel):
    """Candidate work preferences used during deterministic matching and question answering."""
    okay_with_five_day_office: Optional[bool] = True
    willing_to_relocate: Optional[bool] = True

    model_config = ConfigDict(extra="allow")


class ProfileSchema(BaseModel):
    """
    Authoritative candidate profile schema representing data/profile.json.
    
    Includes contact info, target titles, technical skills, employment history,
    education, preferences, and portfolio/social links.
    """
    name: str = Field(..., min_length=1, description="Candidate full name")
    email: str = Field(..., min_length=3, description="Candidate email address")
    phone: str = Field(..., min_length=3, description="Candidate phone number")
    location: str = Field(..., min_length=1, description="Candidate current location (city, state, country)")
    target_roles: List[str] = Field(default_factory=list, description="List of targeted job titles")
    skills: List[str] = Field(default_factory=list, description="Primary technical and domain skills")
    years_of_experience: Union[int, float] = Field(0, description="Total professional experience in years")
    education: List[Dict[str, Any]] = Field(default_factory=list, description="Educational background entries")
    preferred_locations: List[str] = Field(default_factory=list, description="Preferred employment locations")
    remote_preference: str = Field("", description="Remote work preference: Remote, Hybrid, or Onsite")
    minimum_salary: str = Field("", description="Target or minimum acceptable salary expectation")
    notice_period: str = Field("", description="Availability timeline or notice period")
    work_authorization: str = Field("", description="Citizenship or visa authorization status")
    application_preferences: Optional[Dict[str, Any]] = None
    summary: str = Field("", description="Executive summary / candidate bio")
    experience: List[Dict[str, Any]] = Field(default_factory=list, description="Work experience history")
    projects: Optional[List[Dict[str, Any]]] = None
    github: Optional[str] = Field(None, description="GitHub profile URL")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    portfolio: Optional[str] = Field(None, description="Portfolio website URL")

    # Preserve any unknown or custom fields added by the user
    model_config = ConfigDict(extra="allow")

