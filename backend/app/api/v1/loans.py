from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.errors import ResourceNotFoundException
from app.models.loan import Instalment, Loan
from app.models.user import User
from app.schemas.application import LoanResponse

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.get("/active", response_model=Optional[LoanResponse])
async def get_active_loan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the currently active or pending loan for the logged-in customer.
    """
    stmt = (
        select(Loan)
        .where(Loan.user_id == current_user.id, Loan.status.in_(["ACTIVE", "OVERDUE", "PENDING_DISBURSEMENT"]))
        .options(selectinload(Loan.instalments))
        .order_by(Loan.created_at.desc())
    )
    result = await db.execute(stmt)
    loan = result.scalars().first()
    if not loan:
        return None

    # Format instalments
    return loan


@router.get("/{id}", response_model=LoanResponse)
async def get_loan_by_id(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Loan)
        .where(Loan.id == id, Loan.user_id == current_user.id)
        .options(selectinload(Loan.instalments))
    )
    result = await db.execute(stmt)
    loan = result.scalars().first()
    if not loan:
        raise ResourceNotFoundException("Loan", id)
    return loan
