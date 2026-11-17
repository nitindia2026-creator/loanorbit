from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.bank import BankVerification
from app.models.user import User
from app.providers.bank import bank_provider
from app.schemas.kyc import BankVerificationRequest, BankVerificationResponse

router = APIRouter(prefix="/bank-verification", tags=["Bank Verification"])


@router.get("/status", response_model=Optional[BankVerificationResponse])
async def get_bank_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(BankVerification)
        .where(BankVerification.user_id == current_user.id)
        .order_by(BankVerification.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@router.post("/verify", response_model=BankVerificationResponse)
async def verify_bank_account(
    payload: BankVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Simulated penny-drop bank verification with deterministic outcomes.
    """
    mock_res = bank_provider.verify_account(
        account_holder_name=payload.account_holder_name,
        bank_name=payload.bank_name,
        account_number=payload.account_number,
        ifsc_code=payload.ifsc_code,
    )

    masked_acc = f"XXXXXX{payload.account_number[-4:]}" if len(payload.account_number) >= 4 else "XXXX"

    record = BankVerification(
        user_id=current_user.id,
        account_holder_name=payload.account_holder_name,
        bank_name=payload.bank_name,
        account_number_masked=masked_acc,
        ifsc_code=payload.ifsc_code,
        status=mock_res["status"],
        penny_drop_reference=mock_res.get("penny_drop_reference"),
        verified_at=datetime.now(timezone.utc) if mock_res["status"] == "VERIFIED" else None,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record
