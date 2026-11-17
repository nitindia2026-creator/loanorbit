from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.errors import BusinessLogicException, ResourceNotFoundException
from app.financial.allocation import allocate_payment_waterfall
from app.financial.ledger import create_balanced_journal_entry
from app.financial.prepayment import calculate_foreclosure_quote
from app.models.ledger import JournalEntry, JournalLine, LedgerAccount
from app.models.loan import Instalment, Loan
from app.models.repayment import Payment, PaymentAllocation
from app.models.user import User
from app.providers.payment import payment_provider
from app.schemas.application import ForeclosureQuoteResponse, RepaymentRequest

router = APIRouter(prefix="/repayments", tags=["Repayments & Payments"])


@router.post("/pay")
async def process_repayment(
    payload: RepaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes mock UPI repayment.
    Allocates payment via priority waterfall: Charges -> Interest -> Principal.
    Posts balanced journal entry in general ledger.
    """
    stmt = (
        select(Loan)
        .where(Loan.id == payload.loan_id, Loan.user_id == current_user.id)
        .options(selectinload(Loan.instalments))
    )
    result = await db.execute(stmt)
    loan = result.scalar_one_or_none()
    if not loan:
        raise ResourceNotFoundException("Loan", payload.loan_id)

    if loan.status not in ["ACTIVE", "OVERDUE"]:
        raise BusinessLogicException(f"Loan is not in repayable state (current: {loan.status}).")

    # 1. Simulate mock payment provider
    mock_res = payment_provider.initiate_upi_payment(
        loan_id=loan.id,
        amount_paise=payload.amount_paise,
        scenario=payload.scenario,
    )

    payment = Payment(
        loan_id=loan.id,
        amount_paise=payload.amount_paise,
        payment_method="UPI_MOCK",
        status=mock_res["status"],
        provider_reference=mock_res.get("provider_reference"),
        paid_at=datetime.now(timezone.utc),
    )
    db.add(payment)
    await db.flush()

    if mock_res["status"] != "SUCCESS":
        await db.commit()
        return {
            "success": False,
            "status": mock_res["status"],
            "failure_reason": mock_res.get("failure_reason"),
            "payment_id": payment.id,
        }

    # 2. Run allocation waterfall against pending instalments
    inst_dicts = []
    for inst in sorted(loan.instalments, key=lambda x: x.instalment_number):
        if inst.status != "PAID":
            inst_dicts.append({
                "id": inst.id,
                "instalment_number": inst.instalment_number,
                "interest_component_paise": inst.interest_component_paise,
                "principal_component_paise": inst.principal_component_paise,
                "paid_interest_paise": inst.paid_interest_paise,
                "paid_principal_paise": inst.paid_principal_paise,
                "charges_paise": 0,
            })

    allocations, excess_paise = allocate_payment_waterfall(payload.amount_paise, inst_dicts)

    total_alloc_principal = 0
    total_alloc_interest = 0

    inst_map = {inst.id: inst for inst in loan.instalments}

    for alloc in allocations:
        inst = inst_map[alloc["instalment_id"]]
        inst.paid_principal_paise += alloc["allocated_principal_paise"]
        inst.paid_interest_paise += alloc["allocated_interest_paise"]
        inst.outstanding_amount_paise = max(
            0,
            (inst.principal_component_paise + inst.interest_component_paise)
            - (inst.paid_principal_paise + inst.paid_interest_paise)
        )
        if inst.outstanding_amount_paise == 0:
            inst.status = "PAID"
        else:
            inst.status = "PARTIALLY_PAID"

        db_alloc = PaymentAllocation(
            payment_id=payment.id,
            instalment_id=inst.id,
            allocated_principal_paise=alloc["allocated_principal_paise"],
            allocated_interest_paise=alloc["allocated_interest_paise"],
            allocated_charges_paise=alloc["allocated_charges_paise"],
        )
        db.add(db_alloc)

        total_alloc_principal += alloc["allocated_principal_paise"]
        total_alloc_interest += alloc["allocated_interest_paise"]

    # Update loan balances
    loan.outstanding_principal_paise = max(0, loan.outstanding_principal_paise - total_alloc_principal)
    loan.outstanding_interest_paise = max(0, loan.outstanding_interest_paise - total_alloc_interest)

    if loan.outstanding_principal_paise == 0 and loan.outstanding_interest_paise == 0:
        loan.status = "CLOSED"
        loan.closed_at = datetime.now(timezone.utc)

    # 3. Post General Ledger Entry
    acc_stmt = select(LedgerAccount).where(LedgerAccount.account_code.in_(["1001", "1101", "4001"]))
    acc_res = await db.execute(acc_stmt)
    accounts = {a.account_code: a for a in acc_res.scalars().all()}

    if "1001" not in accounts:
        a = LedgerAccount(account_code="1001", account_name="Cash Settlement Pool", account_type="ASSET")
        db.add(a); await db.flush(); accounts["1001"] = a
    if "1101" not in accounts:
        a = LedgerAccount(account_code="1101", account_name="Loan Principal Receivable", account_type="ASSET")
        db.add(a); await db.flush(); accounts["1101"] = a
    if "4001" not in accounts:
        a = LedgerAccount(account_code="4001", account_name="Interest Income", account_type="REVENUE")
        db.add(a); await db.flush(); accounts["4001"] = a

    entry_data = create_balanced_journal_entry(
        entry_reference=f"JRN-PAY-{payment.id[:8].upper()}",
        entry_type="REPAYMENT",
        description=f"Repayment for loan {loan.loan_reference}",
        debits=[{"account_id": accounts["1001"].id, "amount_paise": payload.amount_paise}],
        credits=[
            {"account_id": accounts["1101"].id, "amount_paise": total_alloc_principal},
            {"account_id": accounts["4001"].id, "amount_paise": total_alloc_interest + excess_paise},
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
        db.add(JournalLine(
            journal_entry_id=journal.id,
            account_id=line["account_id"],
            entry_direction=line["entry_direction"],
            amount_paise=line["amount_paise"],
        ))

    await db.commit()
    return {
        "success": True,
        "payment_id": payment.id,
        "status": "SUCCESS",
        "allocated_principal_paise": total_alloc_principal,
        "allocated_interest_paise": total_alloc_interest,
        "outstanding_principal_paise": loan.outstanding_principal_paise,
        "outstanding_interest_paise": loan.outstanding_interest_paise,
        "loan_status": loan.status,
    }


@router.get("/foreclose-quote/{loan_id}", response_model=ForeclosureQuoteResponse)
async def get_foreclosure_quote(
    loan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Loan).where(Loan.id == loan_id, Loan.user_id == current_user.id)
    result = await db.execute(stmt)
    loan = result.scalar_one_or_none()
    if not loan:
        raise ResourceNotFoundException("Loan", loan_id)

    quote = calculate_foreclosure_quote(
        outstanding_principal_paise=loan.outstanding_principal_paise,
        accrued_interest_paise=min(100000, loan.outstanding_interest_paise),
        outstanding_penalties_paise=loan.outstanding_penalties_paise,
    )
    return {"loan_id": loan.id, **quote}
