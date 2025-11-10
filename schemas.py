"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


class CVExperience(BaseModel):
    company: str = Field(..., description="Company name")
    role: str = Field(..., description="Job title / role")
    duration: str = Field(..., description="Duration, e.g., Jan 2020 – Mar 2023")
    achievements: List[str] = Field(default_factory=list, description="Bullet achievements")


class CVEducation(BaseModel):
    degree: str = Field(..., description="Degree title")
    institution: str = Field(..., description="Institution name")
    year: str = Field(..., description="Graduation year")


class CVProfile(BaseModel):
    """
    CV profiles submitted by users.
    Collection name: "cvprofile" (lowercase of class name)
    """
    full_name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn URL")
    summary: Optional[str] = Field(None, description="Career objective or professional summary")
    job_title_target: str = Field(..., description="Target job title")
    skills: List[str] = Field(default_factory=list, description="List of skills")
    experience: List[CVExperience] = Field(default_factory=list, description="Work experience items")
    education: List[CVEducation] = Field(default_factory=list, description="Education items")
    certifications: Optional[List[str]] = Field(default_factory=list, description="Certifications")
    projects: Optional[List[str]] = Field(default_factory=list, description="Projects or achievements")
    languages: Optional[List[str]] = Field(default_factory=list, description="Languages")
    interests: Optional[List[str]] = Field(default_factory=list, description="Interests")
    template: Optional[str] = Field("modern", description="Template style selector")
