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
from app.core.errors import ResourceNotFoundException
from app.models.loan import Loan
from app.models.offer import LoanOffer
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


@router.get("/kfs/{offer_id}")
async def generate_kfs_pdf(
    offer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates server-side simulated Key Fact Statement (KFS) PDF.
    Contains mandatory watermark: 'LOANORBIT DEMO — NOT A REAL LOAN DOCUMENT'
    """
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

    # Table of terms
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
