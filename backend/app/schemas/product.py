from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LoanProductVersionResponse(BaseModel):
    id: str
    version_number: int
    min_principal_paise: int
    max_principal_paise: int
    available_tenures_months: str
    annual_nominal_interest_rate_bps: int
    processing_fee_type: str
    processing_fee_value: int
    gst_rate_bps: int
    late_charge_daily_bps: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoanProductResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    is_active: bool
    created_at: datetime
    versions: List[LoanProductVersionResponse] = []

    class Config:
        from_attributes = True


class CalculatorRequest(BaseModel):
    product_version_id: Optional[str] = None
    principal_paise: int = Field(..., gt=0)
    tenure_months: int = Field(..., gt=0)
    annual_rate_bps: int = Field(default=1800, ge=0)
    fee_type: str = Field(default="PERCENTAGE")
    fee_value: int = Field(default=200, ge=0)
    gst_rate_bps: int = Field(default=1800, ge=0)


class CalculatorResponse(BaseModel):
    principal_paise: int
    tenure_months: int
    annual_nominal_interest_rate_bps: int
    monthly_emi_paise: int
    total_interest_paise: int
    processing_fee_paise: int
    gst_paise: int
    net_disbursement_paise: int
    total_repayable_paise: int
    apr_percent: float
    schedule: List[Dict[str, Any]]
