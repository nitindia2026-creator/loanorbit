from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ApplicationCreate(BaseModel):
    product_version_id: str
    requested_amount_paise: int = Field(..., gt=0)
    requested_tenure_months: int = Field(..., gt=0)
    purpose: str = Field(..., min_length=3)


class ApplicationResponse(BaseModel):
    id: str
    application_reference: str
    user_id: str
    product_version_id: str
    requested_amount_paise: int
    requested_tenure_months: int
    purpose: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UnderwritingDecisionRequest(BaseModel):
    decision: str = Field(..., pattern=r"^(APPROVED|REJECTED|ADDITIONAL_INFO_REQUIRED)$")
    approved_amount_paise: Optional[int] = None
    approved_tenure_months: Optional[int] = None
    approved_rate_bps: Optional[int] = None
    remarks: str = Field(..., min_length=3)


class LoanOfferResponse(BaseModel):
    id: str
    application_id: str
    offer_reference: str
    offered_amount_paise: int
    tenure_months: int
    annual_nominal_interest_rate_bps: int
    monthly_emi_paise: int
    processing_fee_paise: int
    gst_paise: int
    net_disbursement_paise: int
    total_repayable_paise: int
    apr_bps: int
    status: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class InstalmentResponse(BaseModel):
    id: str
    instalment_number: int
    due_date: date
    opening_principal_paise: int
    emi_amount_paise: int
    principal_component_paise: int
    interest_component_paise: int
    closing_principal_paise: int
    paid_principal_paise: int
    paid_interest_paise: int
    outstanding_amount_paise: int
    status: str

    class Config:
        from_attributes = True


class LoanResponse(BaseModel):
    id: str
    loan_reference: str
    user_id: str
    application_id: str
    offer_id: str
    principal_paise: int
    outstanding_principal_paise: int
    outstanding_interest_paise: int
    outstanding_penalties_paise: int
    status: str
    disbursed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    instalments: List[InstalmentResponse] = []

    class Config:
        from_attributes = True


class RepaymentRequest(BaseModel):
    loan_id: str
    amount_paise: int = Field(..., gt=0)
    scenario: str = Field(default="SUCCESS", pattern=r"^(SUCCESS|FAILURE|PENDING)$")


class ForeclosureQuoteResponse(BaseModel):
    loan_id: str
    outstanding_principal_paise: int
    accrued_interest_paise: int
    outstanding_penalties_paise: int
    foreclosure_fee_paise: int
    total_settlement_paise: int
