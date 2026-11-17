from datetime import datetime, timedelta, timezone
import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_admin, require_permission
from app.core.database import get_db
from app.core.errors import BusinessLogicException, ResourceNotFoundException
from app.core.permissions import PermissionEnum
from app.financial.apr import calculate_irr_apr
from app.financial.emi import calculate_fee_and_gst, calculate_monthly_emi
from app.financial.schedule import generate_amortisation_schedule
from app.models.application import LoanApplication, UnderwritingDecision
from app.models.offer import LoanOffer
from app.models.product import LoanProductVersion
from app.models.user import AdminUser
from app.schemas.application import ApplicationResponse, UnderwritingDecisionRequest

router = APIRouter(prefix="/underwriting", tags=["Underwriting Desk"])


@router.get("/queue", response_model=List[ApplicationResponse])
async def list_pending_applications(
    admin: AdminUser = Depends(require_permission(PermissionEnum.APPLICATION_READ)),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns applications awaiting underwriter credit review.
    """
    stmt = (
        select(LoanApplication)
        .where(LoanApplication.status == "UNDER_REVIEW")
        .order_by(LoanApplication.created_at.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/{application_id}/decision")
async def record_underwriting_decision(
    application_id: str,
    payload: UnderwritingDecisionRequest,
    admin: AdminUser = Depends(require_permission(PermissionEnum.APPLICATION_DECIDE)),
    db: AsyncSession = Depends(get_db),
):
    """
    Records credit underwriting decision.
    If APPROVED, atomically creates a versioned LoanOffer.
    """
    stmt = (
        select(LoanApplication)
        .where(LoanApplication.id == application_id)
        .options(selectinload(LoanApplication.product_version))
    )
    result = await db.execute(stmt)
    app = result.scalar_one_or_none()
    if not app:
        raise ResourceNotFoundException("LoanApplication", application_id)

    if app.status != "UNDER_REVIEW":
        raise BusinessLogicException(f"Application cannot be decided in status '{app.status}'.")

    # Record Underwriting Decision
    decision_record = UnderwritingDecision(
        application_id=app.id,
        underwriter_id=admin.id,
        decision=payload.decision,
        approved_amount_paise=payload.approved_amount_paise or app.requested_amount_paise,
        approved_tenure_months=payload.approved_tenure_months or app.requested_tenure_months,
        approved_rate_bps=payload.approved_rate_bps or app.product_version.annual_nominal_interest_rate_bps,
        remarks=payload.remarks,
        policy_version="POL-v1.0-DEMO",
    )
    db.add(decision_record)

    if payload.decision == "APPROVED":
        app.status = "APPROVED"
        principal = payload.approved_amount_paise or app.requested_amount_paise
        tenure = payload.approved_tenure_months or app.requested_tenure_months
        rate_bps = payload.approved_rate_bps or app.product_version.annual_nominal_interest_rate_bps

        # Calculate EMI, Fee, GST, and APR
        emi = calculate_monthly_emi(principal, rate_bps, tenure)
        fee_paise, gst_paise, net_disb = calculate_fee_and_gst(
            principal,
            app.product_version.processing_fee_type,
            app.product_version.processing_fee_value,
            app.product_version.gst_rate_bps,
        )

        schedule = generate_amortisation_schedule(principal, rate_bps, tenure, datetime.now(timezone.utc).date())
        total_repayable = sum(s["emi_amount_paise"] for s in schedule)
        cash_flows = [-float(net_disb) / 100.0] + [float(s["emi_amount_paise"]) / 100.0 for s in schedule]
        apr_pct = calculate_irr_apr(cash_flows)

        offer = LoanOffer(
            application_id=app.id,
            offer_reference=f"OFR-{uuid.uuid4().hex[:8].upper()}",
            offered_amount_paise=principal,
            tenure_months=tenure,
            annual_nominal_interest_rate_bps=rate_bps,
            monthly_emi_paise=emi,
            processing_fee_paise=fee_paise,
            gst_paise=gst_paise,
            net_disbursement_paise=net_disb,
            total_repayable_paise=total_repayable,
            apr_bps=int(apr_pct * 100),
            status="ISSUED",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db.add(offer)

    elif payload.decision == "REJECTED":
        app.status = "REJECTED"
    elif payload.decision == "ADDITIONAL_INFO_REQUIRED":
        app.status = "INFO_REQUESTED"

    await db.commit()
    return {"success": True, "application_status": app.status}
