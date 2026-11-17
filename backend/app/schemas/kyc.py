from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class KYCDocumentResponse(BaseModel):
    id: str
    doc_type: str
    file_path: str
    file_size_bytes: int
    mime_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class KYCCaseResponse(BaseModel):
    id: str
    user_id: str
    id_type: str
    id_number_masked: str
    status: str
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    documents: List[KYCDocumentResponse] = []

    class Config:
        from_attributes = True


class KYCDecisionRequest(BaseModel):
    decision: str = Field(..., pattern=r"^(VERIFIED|REJECTED|RESUBMISSION_REQUESTED)$")
    reason_code: Optional[str] = None
    remarks: str = Field(..., min_length=3)


class BankVerificationRequest(BaseModel):
    account_holder_name: str = Field(..., min_length=2)
    bank_name: str = Field(..., min_length=2)
    account_number: str = Field(..., min_length=8, max_length=20)
    ifsc_code: str = Field(..., pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")


class BankVerificationResponse(BaseModel):
    id: str
    user_id: str
    account_holder_name: str
    bank_name: str
    account_number_masked: str
    ifsc_code: str
    status: str
    penny_drop_reference: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
