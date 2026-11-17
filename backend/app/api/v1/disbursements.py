from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_admin, require_permission
from app.core.database import get_db
from app.core.errors import BusinessLogicException, ResourceNotFoundException
from app.core.permissions import PermissionEnum
from app.financial.ledger import create_balanced_journal_entry
from app.models.bank import BankVerification
from app.models.ledger import JournalEntry, JournalLine, LedgerAccount
from app.models.loan import Loan
from app.models.repayment import Disbursement
from app.models.user import AdminUser
from app.providers.lender import lender_provider

router = APIRouter(prefix="/disbursements", tags=["Disbursements"])


@router.post("/trigger/{loan_id}")
async def trigger_disbursement(
    loan_id: str,
    idempotency_key: str = Header(None),
    admin: AdminUser = Depends(require_permission(PermissionEnum.DISBURSEMENT_TRIGGER)),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes mock disbursement for a loan in PENDING_DISBURSEMENT state.
    Updates loan status to ACTIVE only upon successful mock confirmation.
    Posts balanced General Ledger journal entries.
    """
    stmt = (
        select(Loan)
        .where(Loan.id == loan_id)
        .options(selectinload(Loan.offer), selectinload(Loan.application))
    )
    result = await db.execute(stmt)
    loan = result.scalar_one_or_none()
    if not loan:
        raise ResourceNotFoundException("Loan", loan_id)

    if loan.status != "PENDING_DISBURSEMENT":
        raise BusinessLogicException(f"Loan is not awaiting disbursement (current: {loan.status}).")

    # Fetch verified bank account
    bank_stmt = (
        select(BankVerification)
        .where(BankVerification.user_id == loan.user_id, BankVerification.status == "VERIFIED")
        .order_by(BankVerification.created_at.desc())
    )
    bank_res = await db.execute(bank_stmt)
    bank_acc = bank_res.scalar_one_or_none()
    if not bank_acc:
        raise BusinessLogicException("Borrower has no verified bank account for disbursement.")

    offer = loan.offer
    net_disb_paise = offer.net_disbursement_paise

    # Call mock lender provider
    mock_res = lender_provider.disburse(
        loan_reference=loan.loan_reference,
        amount_paise=net_disb_paise,
        account_number=bank_acc.account_number_masked,
        ifsc_code=bank_acc.ifsc_code,
    )

    disbursement_record = Disbursement(
        loan_id=loan.id,
        amount_paise=net_disb_paise,
        bank_verification_id=bank_acc.id,
        mock_provider_reference=mock_res.get("provider_reference"),
        status=mock_res["status"],
        failure_reason=mock_res.get("failure_reason"),
        disbursed_at=datetime.now(timezone.utc) if mock_res["status"] == "SUCCESS" else None,
    )
    db.add(disbursement_record)

    if mock_res["status"] == "SUCCESS":
        loan.status = "ACTIVE"
        loan.disbursed_at = datetime.now(timezone.utc)
        loan.application.status = "DISBURSED"

        # Look up or create ledger accounts for double-entry posting
        # 1101: Loan Principal Receivable (Asset)
        # 1001: Cash Settlement Account (Asset)
        # 4002: Processing Fee Income (Revenue)
        # 2101: GST Payable (Liability)
        accounts_to_fetch = ["1101", "1001", "4002", "2101"]
        acc_stmt = select(LedgerAccount).where(LedgerAccount.account_code.in_(accounts_to_fetch))
        acc_res = await db.execute(acc_stmt)
        accounts = {a.account_code: a for a in acc_res.scalars().all()}

        # Create accounts if not seeded yet
        if "1101" not in accounts:
            a = LedgerAccount(account_code="1101", account_name="Loan Principal Receivable", account_type="ASSET")
            db.add(a); await db.flush(); accounts["1101"] = a
        if "1001" not in accounts:
            a = LedgerAccount(account_code="1001", account_name="Cash Settlement Pool", account_type="ASSET")
            db.add(a); await db.flush(); accounts["1001"] = a
        if "4002" not in accounts:
            a = LedgerAccount(account_code="4002", account_name="Processing Fee Revenue", account_type="REVENUE")
            db.add(a); await db.flush(); accounts["4002"] = a
        if "2101" not in accounts:
            a = LedgerAccount(account_code="2101", account_name="GST Payable", account_type="LIABILITY")
            db.add(a); await db.flush(); accounts["2101"] = a

        # Balanced Journal Entry
        entry_data = create_balanced_journal_entry(
            entry_reference=f"JRN-DISB-{loan.loan_reference}",
            entry_type="DISBURSEMENT",
            description=f"Disbursement for loan {loan.loan_reference}",
            debits=[{"account_id": accounts["1101"].id, "amount_paise": offer.offered_amount_paise}],
            credits=[
                {"account_id": accounts["1001"].id, "amount_paise": net_disb_paise},
                {"account_id": accounts["4002"].id, "amount_paise": offer.processing_fee_paise},
                {"account_id": accounts["2101"].id, "amount_paise": offer.gst_paise},
            ]
        )

        journal = JournalEntry(
            entry_reference=entry_data["entry_reference"],
            entry_type=entry_data["entry_type"],
            description=entry_data["description"],
            posted_at=entry_data["posted_at"],
        )
        db.add(journal)
        await db.flush()

        for line in entry_data["lines"]:
            j_line = JournalLine(
                journal_entry_id=journal.id,
                account_id=line["account_id"],
                entry_direction=line["entry_direction"],
                amount_paise=line["amount_paise"],
            )
            db.add(j_line)

    await db.commit()
    return {
        "success": mock_res["status"] == "SUCCESS",
        "loan_status": loan.status,
        "disbursement_status": mock_res["status"],
        "provider_reference": mock_res.get("provider_reference"),
    }
