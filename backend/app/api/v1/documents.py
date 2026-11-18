import io
from fastapi import APIRouter, Depends, Response
from reportlab.lib.colors import HexColor, lightgrey
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.errors import BusinessLogicException, ResourceNotFoundException
from app.models.loan import Loan
from app.models.offer import LoanOffer
from app.models.repayment import Payment
from app.models.user import User

router = APIRouter(prefix="/documents", tags=["Documents & PDFs"])


def add_watermark(c: canvas.Canvas):
    c.saveState()
    c.setFont("Helvetica-Bold", 36)
    c.setFillColor(lightgrey, alpha=0.3)
    c.translate(300, 400)
    c.rotate(45)
    c.drawCentredString(0, 0, "LOANORBIT DEMO — NOT A REAL LOAN DOCUMENT")
    c.restoreState()


def get_borrower_name(user: User) -> str:
    return "Borrower"


@router.get("/kfs/{offer_id}")
async def generate_kfs_pdf(
    offer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(LoanOffer)
        .where(LoanOffer.id == offer_id)
        .options(selectinload(LoanOffer.application))
    )
    result = await db.execute(stmt)
    offer = result.scalar_one_or_none()
    if not offer or offer.application.user_id != current_user.id:
        raise ResourceNotFoundException("LoanOffer", offer_id)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    add_watermark(c)

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(HexColor("#0f172a"))
    c.drawString(50, 750, "LOANORBIT — KEY FACT STATEMENT (KFS)")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, "Simulated Digital Lending Disclosure Summary")

    y = 690
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "1. Sanctioned Terms")
    c.setFont("Helvetica", 10)

    rows = [
        ("Offer Reference", offer.offer_reference),
        ("Sanctioned Principal", f"Rs. {offer.offered_amount_paise / 100:,.2f}"),
        ("Annual Nominal Rate", f"{offer.annual_nominal_interest_rate_bps / 100:.2f}%"),
        ("Tenure", f"{offer.tenure_months} Months"),
        ("Monthly EMI", f"Rs. {offer.monthly_emi_paise / 100:,.2f}"),
        ("Processing Fee", f"Rs. {offer.processing_fee_paise / 100:,.2f}"),
        ("GST on Processing Fee (18%)", f"Rs. {offer.gst_paise / 100:,.2f}"),
        ("Net Disbursement Amount", f"Rs. {offer.net_disbursement_paise / 100:,.2f}"),
        ("Total Amount Repayable", f"Rs. {offer.total_repayable_paise / 100:,.2f}"),
        ("Annual Percentage Rate (APR)", f"{offer.apr_bps / 100:.2f}%"),
    ]

    for label, val in rows:
        y -= 25
        c.drawString(60, y, label)
        c.drawRightString(540, y, val)

    y -= 50
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(HexColor("#64748b"))
    c.drawString(50, y, "Notice: This document is strictly synthetic for sandbox verification purposes.")

    c.showPage()
    c.save()

    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=KFS_{offer.offer_reference}.pdf"},
    )


@router.get("/sanction-letter/{offer_id}")
async def generate_sanction_letter_pdf(
    offer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(LoanOffer)
        .where(LoanOffer.id == offer_id)
        .options(selectinload(LoanOffer.application))
    )
    result = await db.execute(stmt)
    offer = result.scalar_one_or_none()
    if not offer or offer.application.user_id != current_user.id:
        raise ResourceNotFoundException("LoanOffer", offer_id)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    add_watermark(c)

    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(HexColor("#0f172a"))
    c.drawString(50, 750, "LOANORBIT — FORMAL SANCTION LETTER")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, f"Date: {offer.created_at.strftime('%d-%b-%Y')} | Ref: {offer.offer_reference}")

    y = 690
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Dear Customer,")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "We are pleased to inform you that your digital personal loan has been conditionally approved.")

    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Key Loan Terms:")
    c.setFont("Helvetica", 10)

    rows = [
        ("Applicant Name", get_borrower_name(current_user)),
        ("Phone Number", current_user.mobile_number),
        ("Sanctioned Amount", f"Rs. {offer.offered_amount_paise / 100:,.2f}"),
        ("Interest Rate (p.a.)", f"{offer.annual_nominal_interest_rate_bps / 100:.2f}% (Reducing Balance)"),
        ("Loan Tenure", f"{offer.tenure_months} Months"),
        ("Equated Monthly Instalment (EMI)", f"Rs. {offer.monthly_emi_paise / 100:,.2f}"),
        ("Upfront Deductions (Fee + GST)", f"Rs. {(offer.processing_fee_paise + offer.gst_paise) / 100:,.2f}"),
        ("Disbursement Net", f"Rs. {offer.net_disbursement_paise / 100:,.2f}"),
    ]
    for label, val in rows:
        y -= 22
        c.drawString(60, y, label)
        c.drawRightString(540, y, val)

    y -= 40
    c.drawString(50, y, "This sanction is subject to agreement acceptance and automated identity verification.")
    y -= 30
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Authorized Signatory: LOANORBIT Credit Operations (Simulated)")

    c.showPage()
    c.save()
    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Sanction_{offer.offer_reference}.pdf"},
    )


@router.get("/agreement/{loan_id}")
async def generate_loan_agreement_pdf(
    loan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Loan).where(Loan.id == loan_id, Loan.user_id == current_user.id).options(selectinload(Loan.offer))
    result = await db.execute(stmt)
    loan = result.scalar_one_or_none()
    if not loan:
        raise ResourceNotFoundException("Loan", loan_id)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    add_watermark(c)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 750, "LOANORBIT — DIGITAL LOAN AGREEMENT")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, f"Loan Reference: {loan.loan_reference} | Status: {loan.status}")

    y = 690
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "This Digital Facility Agreement is entered into between:")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"1. Lender: LOANORBIT Sandbox Lending Partner")
    y -= 15
    c.drawString(50, y, f"2. Borrower: {get_borrower_name(current_user)} ({current_user.mobile_number})")

    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Terms of Agreement:")
    c.setFont("Helvetica", 10)

    rows = [
        ("Loan Reference", loan.loan_reference),
        ("Principal Facility", f"Rs. {loan.principal_paise / 100:,.2f}"),
        ("Disbursed Date", loan.disbursed_at.strftime('%d-%b-%Y') if loan.disbursed_at else "Pending"),
        ("Current Outstanding Principal", f"Rs. {loan.outstanding_principal_paise / 100:,.2f}"),
        ("Current Outstanding Interest", f"Rs. {loan.outstanding_interest_paise / 100:,.2f}"),
        ("Governing Law", "Simulated Jurisdiction / LOANORBIT Sandbox Rules"),
    ]
    for label, val in rows:
        y -= 22
        c.drawString(60, y, label)
        c.drawRightString(540, y, val)

    y -= 50
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, y, "Digitally confirmed via e-sign / OTP consent by borrower in LOANORBIT mobile application.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Agreement_{loan.loan_reference}.pdf"},
    )


@router.get("/receipt/{payment_id}")
async def generate_payment_receipt_pdf(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Payment)
        .join(Loan)
        .where(Payment.id == payment_id, Loan.user_id == current_user.id)
        .options(selectinload(Payment.loan), selectinload(Payment.allocations))
    )
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()
    if not payment:
        raise ResourceNotFoundException("Payment", payment_id)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    add_watermark(c)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 750, "LOANORBIT — REPAYMENT RECEIPT")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, f"Receipt Ref: {payment.id[:12].upper()} | Status: {payment.status}")

    y = 690
    rows = [
        ("Loan Reference", payment.loan.loan_reference),
        ("Payment Date", payment.paid_at.strftime('%d-%b-%Y %H:%M:%S UTC')),
        ("Amount Paid", f"Rs. {payment.amount_paise / 100:,.2f}"),
        ("Payment Method", payment.payment_method),
        ("Provider Reference", payment.provider_reference or "N/A"),
        ("Allocated Principal", f"Rs. {sum(a.allocated_principal_paise for a in payment.allocations) / 100:,.2f}"),
        ("Allocated Interest", f"Rs. {sum(a.allocated_interest_paise for a in payment.allocations) / 100:,.2f}"),
        ("Allocated Charges / Penalties", f"Rs. {sum(a.allocated_charges_paise for a in payment.allocations) / 100:,.2f}"),
        ("Remaining Outstanding Principal", f"Rs. {payment.loan.outstanding_principal_paise / 100:,.2f}"),
    ]
    for label, val in rows:
        y -= 25
        c.setFont("Helvetica-Bold" if "Amount" in label else "Helvetica", 10)
        c.drawString(60, y, label)
        c.drawRightString(540, y, val)

    c.showPage()
    c.save()
    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Receipt_{payment.id[:8]}.pdf"},
    )


@router.get("/noc/{loan_id}")
async def generate_noc_pdf(
    loan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Loan).where(Loan.id == loan_id, Loan.user_id == current_user.id)
    result = await db.execute(stmt)
    loan = result.scalar_one_or_none()
    if not loan:
        raise ResourceNotFoundException("Loan", loan_id)

    if loan.status not in ("CLOSED", "FORECLOSED"):
        raise BusinessLogicException(f"Cannot generate NOC for active or unsettled loan (status: {loan.status}).")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    add_watermark(c)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 750, "LOANORBIT — NO OBJECTION CERTIFICATE (NOC)")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, f"Date: {loan.closed_at.strftime('%d-%b-%Y') if loan.closed_at else 'N/A'}")

    y = 690
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "TO WHOMSOEVER IT MAY CONCERN")
    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"This is to certify that borrower {get_borrower_name(current_user)} has fully repaid and settled")
    y -= 15
    c.drawString(50, y, f"all outstanding financial obligations under Loan Account {loan.loan_reference}.")
    y -= 30

    rows = [
        ("Loan Reference", loan.loan_reference),
        ("Sanctioned Principal", f"Rs. {loan.principal_paise / 100:,.2f}"),
        ("Closure Date", loan.closed_at.strftime('%d-%b-%Y') if loan.closed_at else "Closed"),
        ("Closure Status", loan.status),
        ("Outstanding Balance", "Rs. 0.00"),
    ]
    for label, val in rows:
        y -= 22
        c.drawString(60, y, label)
        c.drawRightString(540, y, val)

    y -= 40
    c.drawString(50, y, "There are no pending dues or claims outstanding against this loan account.")
    y -= 30
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "LOANORBIT Loan Servicing & Collections Desk (Simulated)")

    c.showPage()
    c.save()
    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=NOC_{loan.loan_reference}.pdf"},
    )
