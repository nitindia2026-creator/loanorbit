import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.errors import BusinessLogicException, ResourceNotFoundException
from app.models.application import LoanApplication
from app.models.bank import BankVerification
from app.models.kyc import KYCCase
from app.models.product import LoanProductVersion
from app.models.profile import CustomerProfile
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationResponse

router = APIRouter(prefix="/applications", tags=["Loan Applications"])


@router.get("", response_model=List[ApplicationResponse])
async def list_my_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(LoanApplication)
        .where(LoanApplication.user_id == current_user.id)
        .order_by(LoanApplication.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ApplicationResponse)
async def submit_application(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a new loan application.
    Validates profile, verified KYC status, and verified bank account.
    """
    # 1. Profile verification
    prof_stmt = select(CustomerProfile).where(CustomerProfile.user_id == current_user.id)
    prof_res = await db.execute(prof_stmt)
    if not prof_res.scalar_one_or_none():
        raise BusinessLogicException("Customer profile must be completed before applying.")

    # 2. KYC verification
    kyc_stmt = (
        select(KYCCase)
        .where(KYCCase.user_id == current_user.id, KYCCase.status == "VERIFIED")
        .order_by(KYCCase.created_at.desc())
    )
    kyc_res = await db.execute(kyc_stmt)
    if not kyc_res.scalar_one_or_none():
        raise BusinessLogicException("KYC must be verified before applying for a loan.")

    # 3. Bank verification
    bank_stmt = (
        select(BankVerification)
        .where(BankVerification.user_id == current_user.id, BankVerification.status == "VERIFIED")
        .order_by(BankVerification.created_at.desc())
    )
    bank_res = await db.execute(bank_stmt)
    if not bank_res.scalar_one_or_none():
        raise BusinessLogicException("Bank account must be verified before applying for a loan.")

    # 4. Product version validity
    prod_stmt = select(LoanProductVersion).where(LoanProductVersion.id == payload.product_version_id)
    prod_res = await db.execute(prod_stmt)
    version = prod_res.scalar_one_or_none()
    if not version:
        raise ResourceNotFoundException("LoanProductVersion", payload.product_version_id)

    if payload.requested_amount_paise < version.min_principal_paise or payload.requested_amount_paise > version.max_principal_paise:
        raise BusinessLogicException(
            f"Requested amount must be between ₹{version.min_principal_paise//100} and ₹{version.max_principal_paise//100}."
        )

    ref = f"APP-{uuid.uuid4().hex[:8].upper()}"
    app = LoanApplication(
        application_reference=ref,
        user_id=current_user.id,
        product_version_id=version.id,
        requested_amount_paise=payload.requested_amount_paise,
        requested_tenure_months=payload.requested_tenure_months,
        purpose=payload.purpose,
        status="UNDER_REVIEW",
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app


@router.get("/{id}", response_model=ApplicationResponse)
async def get_application_detail(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(LoanApplication).where(LoanApplication.id == id, LoanApplication.user_id == current_user.id)
    result = await db.execute(stmt)
    app = result.scalar_one_or_none()
    if not app:
        raise ResourceNotFoundException("LoanApplication", id)
    return app
