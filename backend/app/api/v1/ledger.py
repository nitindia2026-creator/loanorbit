from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_admin, require_permission
from app.core.database import get_db
from app.core.permissions import PermissionEnum
from app.models.ledger import JournalEntry, LedgerAccount
from app.models.user import AdminUser
from app.schemas.ledger import JournalEntryResponse, LedgerAccountResponse

router = APIRouter(prefix="/ledger", tags=["General Ledger & Accounting"])


@router.get("/accounts", response_model=List[LedgerAccountResponse])
async def list_ledger_accounts(
    admin: AdminUser = Depends(require_permission(PermissionEnum.LEDGER_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(LedgerAccount).order_by(LedgerAccount.account_code.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/journal-entries", response_model=List[JournalEntryResponse])
async def list_journal_entries(
    admin: AdminUser = Depends(require_permission(PermissionEnum.LEDGER_VIEW)),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(JournalEntry)
        .options(selectinload(JournalEntry.lines))
        .order_by(JournalEntry.posted_at.desc())
        .limit(100)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
