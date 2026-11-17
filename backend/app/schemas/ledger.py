from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class LedgerAccountResponse(BaseModel):
    id: str
    account_code: str
    account_name: str
    account_type: str
    balance_paise: int
    created_at: datetime

    class Config:
        from_attributes = True


class JournalLineResponse(BaseModel):
    id: str
    account_id: str
    entry_direction: str
    amount_paise: int

    class Config:
        from_attributes = True


class JournalEntryResponse(BaseModel):
    id: str
    entry_reference: str
    entry_type: str
    description: str
    posted_at: datetime
    lines: List[JournalLineResponse] = []

    class Config:
        from_attributes = True


class DashboardMetricsResponse(BaseModel):
    total_customers: int
    total_applications: int
    pending_applications: int
    pending_kyc: int
    approved_applications: int
    rejected_applications: int
    active_loans: int
    overdue_loans: int
    total_disbursed_paise: int
    total_repaid_paise: int
    total_outstanding_principal_paise: int


class SupportMessageResponse(BaseModel):
    id: str
    sender_type: str
    sender_id: str
    message: str
    is_internal_note: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SupportTicketResponse(BaseModel):
    id: str
    ticket_reference: str
    user_id: str
    category: str
    subject: str
    description: str
    status: str
    assigned_admin_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[SupportMessageResponse] = []

    class Config:
        from_attributes = True


class SupportTicketCreate(BaseModel):
    category: str
    subject: str
    description: str


class SupportMessageCreate(BaseModel):
    message: str
    is_internal_note: bool = False
