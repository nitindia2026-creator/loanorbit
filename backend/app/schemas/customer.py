from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProfileCreateOrUpdate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    date_of_birth: date
    gender: str = Field(..., pattern=r"^(MALE|FEMALE|OTHER)$")
    address_line1: str = Field(..., min_length=5)
    address_line2: Optional[str] = None
    city: str = Field(..., min_length=2)
    state: str = Field(..., min_length=2)
    pincode: str = Field(..., pattern=r"^\d{6}$")
    employment_type: str = Field(..., pattern=r"^(SALARIED|SELF_EMPLOYED|STUDENT)$")
    monthly_income_paise: int = Field(..., gt=0)
    monthly_expenses_paise: int = Field(..., ge=0)
    employer_name: Optional[str] = None
    employment_duration_months: Optional[int] = Field(None, ge=0)


class ProfileResponse(ProfileCreateOrUpdate):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConsentCreate(BaseModel):
    purpose: str
    policy_version: str = "v1.0"
    status: str = "ACCEPTED"


class ConsentResponse(BaseModel):
    id: str
    user_id: str
    purpose: str
    policy_version: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
