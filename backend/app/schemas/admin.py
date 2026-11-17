from pydantic import BaseModel


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
