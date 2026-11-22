from typing import List
from pydantic import BaseModel, Field, field_validator


class StaffMember(BaseModel):
    id: str
    name: str
    role: str
    skills: List[str] = Field(default_factory=list)
    available_shifts: List[str]
    max_weekly_hours: int = Field(gt=0)
    assigned_weekly_hours: int = Field(default=0, ge=0)

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value):
        return str(value).strip().lower()

    @field_validator("skills", "available_shifts", mode="before")
    @classmethod
    def normalize_lists(cls, value):
        return [str(item).strip().lower() for item in value]


class Shift(BaseModel):
    id: str
    date: str
    shift_type: str
    role_required: str
    required_skills: List[str] = Field(default_factory=list)
    hours: int = Field(gt=0)
    priority: int = Field(default=1, ge=1, le=5)

    @field_validator("shift_type", "role_required", mode="before")
    @classmethod
    def normalize_text(cls, value):
        return str(value).strip().lower()

    @field_validator("required_skills", mode="before")
    @classmethod
    def normalize_skills(cls, value):
        return [str(item).strip().lower() for item in value]


class AllocationRequest(BaseModel):
    staff: List[StaffMember]
    shifts: List[Shift]


class Assignment(BaseModel):
    shift_id: str
    staff_id: str
    staff_name: str
    explanation: str


class UnfilledShift(BaseModel):
    shift_id: str
    reason: str


class AllocationResponse(BaseModel):
    assignments: List[Assignment]
    unfilled_shifts: List[UnfilledShift]
    audit: List[str]
    summary: dict
