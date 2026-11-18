from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_admin, get_current_user, require_permission
from app.core.database import get_db
from app.core.errors import BusinessLogicException, ResourceNotFoundException
from app.core.idempotency import check_idempotency, save_idempotency
from app.core.permissions import PermissionEnum
from app.financial.allocation import allocate_payment_waterfall
from app.financial.ledger import create_balanced_journal_entry
from app.financial.prepayment import calculate_foreclosure_quote
from app.financial.reversal import create_reversal_journal_entry
from app.models.ledger import JournalEntry, JournalLine, LedgerAccount
from app.models.loan import Instalment, Loan
from app.models.repayment import Payment, PaymentAllocation
from app.models.user import AdminUser, User
from app.providers.payment import payment_provider
from app.schemas.application import ForeclosureQuoteResponse, RepaymentRequest

router = APIRouter(prefix="/repayments", tags=["Repayments & Payments"])


class ForeclosureRequest(BaseModel):
    loan_id: str


class ReversalRequest(BaseModel):
    reason: str = "Admin manual reversal"


@router.post("/pay")
async def process_repayment(
    payload: RepaymentRequest,
    idempotency_key: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes mock UPI repayment with idempotency protection.
    Allocates payment via priority waterfall: Charges -> Interest -> Principal.
    Posts balanced journal entry in general ledger.
    """
    # 1. Idempotency Check
    cached = await check_idempotency(db, idempotency_key, "/repayments/pay", payload.model_dump())
    if cached:
        return cached[1]

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

    # 2. Simulate mock payment provider
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
        resp_data = {
            "success": False,
            "status": mock_res["status"],
            "failure_reason": mock_res.get("failure_reason"),
            "payment_id": payment.id,
        }
        await save_idempotency(db, idempotency_key, "/repayments/pay", payload.model_dump(), 200, resp_data)
        await db.commit()
        return resp_data

    # 3. First, handle any overdue loan-level penalties/charges
    remaining_payment = payload.amount_paise
    alloc_charges_total = 0
    if loan.outstanding_penalties_paise > 0:
        alloc_charges_total = min(remaining_payment, loan.outstanding_penalties_paise)
        loan.outstanding_penalties_paise -= alloc_charges_total
        remaining_payment -= alloc_charges_total

    # 4. Run allocation waterfall against pending instalments for remaining amount
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

    allocations, excess_paise = allocate_payment_waterfall(remaining_payment, inst_dicts)

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

    if loan.outstanding_principal_paise == 0 and loan.outstanding_interest_paise == 0 and loan.outstanding_penalties_paise == 0:
        loan.status = "CLOSED"
        loan.closed_at = datetime.now(timezone.utc)
    elif loan.outstanding_penalties_paise == 0 and loan.status == "OVERDUE":
        # Check if overdue instalments are now cleared
        has_overdue = any(i.status == "OVERDUE" for i in loan.instalments)
        if not has_overdue:
            loan.status = "ACTIVE"

    # 5. Post Balanced General Ledger Entry
    acc_codes = ["1001", "1101", "4001", "1103"]
    acc_stmt = select(LedgerAccount).where(LedgerAccount.account_code.in_(acc_codes))
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
    if "1103" not in accounts:
        a = LedgerAccount(account_code="1103", account_name="Penalties Receivable", account_type="ASSET")
        db.add(a); await db.flush(); accounts["1103"] = a

    credits = []
    if total_alloc_principal > 0:
        credits.append({"account_id": accounts["1101"].id, "amount_paise": total_alloc_principal})
    if (total_alloc_interest + excess_paise) > 0:
        credits.append({"account_id": accounts["4001"].id, "amount_paise": total_alloc_interest + excess_paise})
    if alloc_charges_total > 0:
        credits.append({"account_id": accounts["1103"].id, "amount_paise": alloc_charges_total})

    # Assert exact sum
    entry_data = create_balanced_journal_entry(
        entry_reference=f"JRN-PAY-{payment.id[:8].upper()}",
        entry_type="REPAYMENT",
        description=f"Repayment for loan {loan.loan_reference}",
        debits=[{"account_id": accounts["1001"].id, "amount_paise": payload.amount_paise}],
        credits=credits,
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

    resp_data = {
        "success": True,
        "payment_id": payment.id,
        "status": "SUCCESS",
        "allocated_principal_paise": total_alloc_principal,
        "allocated_interest_paise": total_alloc_interest,
        "allocated_charges_paise": alloc_charges_total,
        "outstanding_principal_paise": loan.outstanding_principal_paise,
        "outstanding_interest_paise": loan.outstanding_interest_paise,
        "loan_status": loan.status,
    }

    await save_idempotency(db, idempotency_key, "/repayments/pay", payload.model_dump(), 200, resp_data)
    await db.commit()
    return resp_data


@router.post("/foreclose")
async def execute_foreclosure(
    payload: ForeclosureRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes early foreclosure settlement for the loan.
    Calculates quote, collects mock payoff payment, marks all instalments PAID,
    zeros out balances, and sets loan status to FORECLOSED.
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
        raise BusinessLogicException(f"Loan cannot be foreclosed in state '{loan.status}'.")

    quote = calculate_foreclosure_quote(
        outstanding_principal_paise=loan.outstanding_principal_paise,
        accrued_interest_paise=min(100000, loan.outstanding_interest_paise),
        outstanding_penalties_paise=loan.outstanding_penalties_paise,
    )
    payoff_paise = quote["total_settlement_paise"]

    # Record payment
    payment = Payment(
        loan_id=loan.id,
        amount_paise=payoff_paise,
        payment_method="UPI_MOCK",
        status="SUCCESS",
        provider_reference=f"PAYOFF-{uuid.uuid4().hex[:8].upper()}",
        paid_at=datetime.now(timezone.utc),
    )
    db.add(payment)
    await db.flush()

    # Mark all instalments as PAID
    for inst in loan.instalments:
        inst.paid_principal_paise = inst.principal_component_paise
        inst.paid_interest_paise = inst.interest_component_paise
        inst.outstanding_amount_paise = 0
        inst.status = "PAID"

    # Zero loan balances and close
    p_cleared = loan.outstanding_principal_paise
    i_cleared = quote["accrued_interest_paise"]
    pen_cleared = loan.outstanding_penalties_paise

    loan.outstanding_principal_paise = 0
    loan.outstanding_interest_paise = 0
    loan.outstanding_penalties_paise = 0
    loan.status = "FORECLOSED"
    loan.closed_at = datetime.now(timezone.utc)

    # Post balanced ledger entry
    acc_codes = ["1001", "1101", "4001", "1103"]
    acc_stmt = select(LedgerAccount).where(LedgerAccount.account_code.in_(acc_codes))
    accounts = {a.account_code: a for a in (await db.execute(acc_stmt)).scalars().all()}

    credits = []
    if p_cleared > 0:
        credits.append({"account_id": accounts["1101"].id, "amount_paise": p_cleared})
    if i_cleared > 0:
        credits.append({"account_id": accounts["4001"].id, "amount_paise": i_cleared})
    if pen_cleared > 0:
        credits.append({"account_id": accounts["1103"].id, "amount_paise": pen_cleared})

    entry_data = create_balanced_journal_entry(
        entry_reference=f"JRN-FORECLOSE-{loan.loan_reference}",
        entry_type="REPAYMENT",
        description=f"Full foreclosure settlement for loan {loan.loan_reference}",
        debits=[{"account_id": accounts["1001"].id, "amount_paise": payoff_paise}],
        credits=credits,
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
        "loan_status": "FORECLOSED",
        "settlement_amount_paise": payoff_paise,
        "payment_id": payment.id,
    }


@router.post("/{payment_id}/reverse")
async def reverse_payment(
    payment_id: str,
    payload: ReversalRequest,
    admin: AdminUser = Depends(require_permission(PermissionEnum.REPAYMENT_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    """
    Reverses a previously posted payment.
    Creates exact compensating inverse journal lines in general ledger,
    restores loan and instalment balances, and marks payment REVERSED.
    """
    stmt = (
        select(Payment)
        .where(Payment.id == payment_id)
        .options(selectinload(Payment.allocations), selectinload(Payment.loan).selectinload(Loan.instalments))
    )
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()
    if not payment:
        raise ResourceNotFoundException("Payment", payment_id)

    if payment.status != "SUCCESS":
        raise BusinessLogicException(f"Cannot reverse payment in status '{payment.status}'.")

    loan = payment.loan

    # 1. Revert allocations from instalments
    inst_map = {i.id: i for i in loan.instalments}
    total_rev_principal = 0
    total_rev_interest = 0

    for alloc in payment.allocations:
        inst = inst_map.get(alloc.instalment_id)
        if inst:
            inst.paid_principal_paise = max(0, inst.paid_principal_paise - alloc.allocated_principal_paise)
            inst.paid_interest_paise = max(0, inst.paid_interest_paise - alloc.allocated_interest_paise)
            inst.outstanding_amount_paise = (
                (inst.principal_component_paise + inst.interest_component_paise)
                - (inst.paid_principal_paise + inst.paid_interest_paise)
            )
            inst.status = "PARTIALLY_PAID" if inst.paid_principal_paise > 0 else "SCHEDULED"

        total_rev_principal += alloc.allocated_principal_paise
        total_rev_interest += alloc.allocated_interest_paise

    # 2. Restore loan balances
    loan.outstanding_principal_paise += total_rev_principal
    loan.outstanding_interest_paise += total_rev_interest
    if loan.status in ["CLOSED", "FORECLOSED"]:
        loan.status = "ACTIVE"
        loan.closed_at = None

    # Mark payment as REVERSED
    payment.status = "REVERSED"

    # 3. Create compensating general ledger entry
    orig_ref = f"JRN-PAY-{payment.id[:8].upper()}"
    j_stmt = select(JournalEntry).where(JournalEntry.entry_reference == orig_ref).options(selectinload(JournalEntry.lines))
    orig_journal = (await db.execute(j_stmt)).scalar_one_or_none()

    if orig_journal:
        lines_data = [
            {
                "account_id": l.account_id,
                "entry_direction": l.entry_direction,
                "amount_paise": l.amount_paise,
            }
            for l in orig_journal.lines
        ]
        rev_entry_data = create_reversal_journal_entry(
            original_entry_reference=orig_journal.entry_reference,
            original_lines=lines_data,
            reason=payload.reason,
        )

        rev_journal = JournalEntry(
            entry_reference=rev_entry_data["entry_reference"],
            entry_type=rev_entry_data["entry_type"],
            description=rev_entry_data["description"],
            posted_at=rev_entry_data["posted_at"],
        )
        db.add(rev_journal)
        await db.flush()

        for line in rev_entry_data["lines"]:
            db.add(JournalLine(
                journal_entry_id=rev_journal.id,
                account_id=line["account_id"],
                entry_direction=line["entry_direction"],
                amount_paise=line["amount_paise"],
            ))

    await db.commit()
    return {
        "success": True,
        "payment_status": "REVERSED",
        "loan_status": loan.status,
        "restored_principal_paise": total_rev_principal,
        "restored_interest_paise": total_rev_interest,
    }


@router.get("/all")
async def list_all_payments(
    limit: int = 50,
    admin: AdminUser = Depends(require_permission(PermissionEnum.REPAYMENT_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns recent payment attempts and statuses for admin repayment desk.
    """
    stmt = select(Payment).order_by(Payment.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


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
