from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_admin, require_permission
from app.core.database import get_db
from app.core.errors import ResourceNotFoundException
from app.core.permissions import PermissionEnum
from app.models.application import LoanApplication
from app.models.document import AuditLog
from app.models.kyc import KYCCase, KYCDecision
from app.models.loan import Loan
from app.models.repayment import Disbursement, Payment
from app.models.user import AdminUser, User
from app.schemas.admin import DashboardMetricsResponse
from app.schemas.kyc import KYCCaseResponse, KYCDecisionRequest

router = APIRouter(prefix="/admin", tags=["Admin Operations"])


@router.get("/dashboard", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    admin: AdminUser = Depends(require_permission(PermissionEnum.METRICS_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    """
    Real-time aggregated dashboard metrics from backend database queries.
    Never hardcoded.
    """
    # 1. Total Customers
    cust_cnt = await db.scalar(select(func.count(User.id))) or 0

    # 2. Total Applications & breakdowns
    app_cnt = await db.scalar(select(func.count(LoanApplication.id))) or 0
    pending_apps = await db.scalar(
        select(func.count(LoanApplication.id)).where(LoanApplication.status == "UNDER_REVIEW")
    ) or 0
    approved_apps = await db.scalar(
        select(func.count(LoanApplication.id)).where(LoanApplication.status.in_(["APPROVED", "OFFER_ACCEPTED", "DISBURSED"]))
    ) or 0
    rejected_apps = await db.scalar(
        select(func.count(LoanApplication.id)).where(LoanApplication.status == "REJECTED")
    ) or 0

    # 3. Pending KYC
    pending_kyc = await db.scalar(
        select(func.count(KYCCase.id)).where(KYCCase.status == "PENDING")
    ) or 0

    # 4. Active & Overdue loans
    active_loans = await db.scalar(
        select(func.count(Loan.id)).where(Loan.status == "ACTIVE")
    ) or 0
    overdue_loans = await db.scalar(
        select(func.count(Loan.id)).where(Loan.status == "OVERDUE")
    ) or 0

    # 5. Financial sums
    total_disb = await db.scalar(
        select(func.sum(Disbursement.amount_paise)).where(Disbursement.status == "SUCCESS")
    ) or 0
    total_repaid = await db.scalar(
        select(func.sum(Payment.amount_paise)).where(Payment.status == "SUCCESS")
    ) or 0
    total_outstanding = await db.scalar(
        select(func.sum(Loan.outstanding_principal_paise)).where(Loan.status.in_(["ACTIVE", "OVERDUE"]))
    ) or 0

    return {
        "total_customers": cust_cnt,
        "total_applications": app_cnt,
        "pending_applications": pending_apps,
        "pending_kyc": pending_kyc,
        "approved_applications": approved_apps,
        "rejected_applications": rejected_apps,
        "active_loans": active_loans,
        "overdue_loans": overdue_loans,
        "total_disbursed_paise": total_disb,
        "total_repaid_paise": total_repaid,
        "total_outstanding_principal_paise": total_outstanding,
    }


@router.get("/kyc/queue", response_model=List[KYCCaseResponse])
async def list_kyc_queue(
    admin: AdminUser = Depends(require_permission(PermissionEnum.KYC_REVIEW)),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(KYCCase)
        .where(KYCCase.status == "PENDING")
        .options(selectinload(KYCCase.documents))
        .order_by(KYCCase.created_at.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/kyc/{id}/decision")
async def record_kyc_officer_decision(
    id: str,
    payload: KYCDecisionRequest,
    admin: AdminUser = Depends(require_permission(PermissionEnum.KYC_DECIDE)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(KYCCase).where(KYCCase.id == id)
    result = await db.execute(stmt)
    case = result.scalar_one_or_none()
    if not case:
        raise ResourceNotFoundException("KYCCase", id)

    case.status = payload.decision
    if payload.decision == "REJECTED":
        case.rejection_reason = payload.remarks

    decision = KYCDecision(
        kyc_case_id=case.id,
        officer_id=admin.id,
        decision=payload.decision,
        reason_code=payload.reason_code,
        remarks=payload.remarks,
    )
    db.add(decision)
    await db.commit()
    return {"success": True, "kyc_status": case.status}


@router.get("/audit-logs")
async def list_audit_logs(
    limit: int = Query(50, le=200),
    admin: AdminUser = Depends(require_permission(PermissionEnum.AUDIT_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/customers")
async def list_all_customers(
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    admin: AdminUser = Depends(require_permission(PermissionEnum.CUSTOMER_READ)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).options(selectinload(User.profile)).order_by(User.created_at.desc()).limit(limit).offset(offset)
    if search:
        stmt = stmt.where(User.mobile_number.ilike(f"%{search}%"))
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users
