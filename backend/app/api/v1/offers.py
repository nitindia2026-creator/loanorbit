from datetime import datetime, timezone
from typing import Optional
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.errors import BusinessLogicException, ResourceNotFoundException
from app.financial.schedule import generate_amortisation_schedule
from app.models.application import LoanApplication
from app.models.loan import Instalment, Loan
from app.models.offer import LoanOffer
from app.models.user import User
from app.schemas.application import LoanOfferResponse

router = APIRouter(prefix="/offers", tags=["Loan Offers"])


@router.get("/my-pending", response_model=Optional[LoanOfferResponse])
async def get_my_pending_offer(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns latest active ISSUED offer for the current customer, if any.
    """
    stmt = (
        select(LoanOffer)
        .join(LoanApplication)
        .where(
            LoanApplication.user_id == current_user.id,
            LoanOffer.status == "ISSUED",
        )
        .order_by(LoanOffer.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().first()


@router.get("/{id}", response_model=LoanOfferResponse)
async def get_offer(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(LoanOffer)
        .join(LoanApplication)
        .where(LoanOffer.id == id, LoanApplication.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    offer = result.scalar_one_or_none()
    if not offer:
        raise ResourceNotFoundException("LoanOffer", id)
    return offer


@router.post("/{id}/accept")
async def accept_loan_offer(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Accepts loan offer, marks application OFFER_ACCEPTED, and creates Loan in PENDING_DISBURSEMENT state.
    """
    stmt = (
        select(LoanOffer)
        .join(LoanApplication)
        .where(LoanOffer.id == id, LoanApplication.user_id == current_user.id)
        .options(selectinload(LoanOffer.application))
    )
    result = await db.execute(stmt)
    offer = result.scalar_one_or_none()
    if not offer:
        raise ResourceNotFoundException("LoanOffer", id)

    if offer.status != "ISSUED":
        raise BusinessLogicException(f"Offer is not in ISSUED state (current: {offer.status}).")

    expires_at = offer.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at and expires_at < datetime.now(timezone.utc):
        offer.status = "EXPIRED"
        await db.commit()
        raise BusinessLogicException("Loan offer has expired.")

    offer.status = "ACCEPTED"
    offer.application.status = "OFFER_ACCEPTED"

    # Create Loan Record in PENDING_DISBURSEMENT
    loan = Loan(
        loan_reference=f"LON-{uuid.uuid4().hex[:8].upper()}",
        user_id=current_user.id,
        application_id=offer.application_id,
        offer_id=offer.id,
        principal_paise=offer.offered_amount_paise,
        outstanding_principal_paise=offer.offered_amount_paise,
        outstanding_interest_paise=offer.total_repayable_paise - offer.offered_amount_paise,
        outstanding_penalties_paise=0,
        status="PENDING_DISBURSEMENT",
    )
    db.add(loan)
    await db.flush()

    # Pre-generate repayment schedule instalments
    schedule = generate_amortisation_schedule(
        principal_paise=offer.offered_amount_paise,
        annual_rate_bps=offer.annual_nominal_interest_rate_bps,
        tenure_months=offer.tenure_months,
        start_date=datetime.now(timezone.utc).date(),
    )

    for item in schedule:
        inst = Instalment(
            loan_id=loan.id,
            instalment_number=item["instalment_number"],
            due_date=item["due_date"],
            opening_principal_paise=item["opening_principal_paise"],
            emi_amount_paise=item["emi_amount_paise"],
            principal_component_paise=item["principal_component_paise"],
            interest_component_paise=item["interest_component_paise"],
            closing_principal_paise=item["closing_principal_paise"],
            outstanding_amount_paise=item["outstanding_amount_paise"],
            status="SCHEDULED",
        )
        db.add(inst)

    await db.commit()
    return {
        "success": True,
        "loan_id": loan.id,
        "loan_reference": loan.loan_reference,
        "status": loan.status,
    }


@router.post("/{id}/reject")
async def reject_loan_offer(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(LoanOffer)
        .join(LoanApplication)
        .where(LoanOffer.id == id, LoanApplication.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    offer = result.scalar_one_or_none()
    if not offer:
        raise ResourceNotFoundException("LoanOffer", id)

    offer.status = "REJECTED"
    await db.commit()
    return {"success": True, "status": "REJECTED"}
