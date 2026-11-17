from datetime import date
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.financial.apr import calculate_irr_apr
from app.financial.emi import calculate_fee_and_gst, calculate_monthly_emi
from app.financial.schedule import generate_amortisation_schedule
from app.models.product import LoanProduct, LoanProductVersion
from app.models.profile import CustomerProfile
from app.models.user import User
from app.schemas.product import (
    CalculatorRequest,
    CalculatorResponse,
    LoanProductResponse,
)

router = APIRouter(prefix="/products", tags=["Loan Products & Calculator"])


@router.get("", response_model=List[LoanProductResponse])
async def list_active_products(db: AsyncSession = Depends(get_db)):
    """
    Returns all active loan products with their active versions.
    """
    stmt = (
        select(LoanProduct)
        .where(LoanProduct.is_active == True)
        .options(selectinload(LoanProduct.versions))
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/calculate", response_model=CalculatorResponse)
async def calculate_loan(payload: CalculatorRequest):
    """
    Backend-backed loan calculator computing exact EMI, fees, GST, APR, and schedule.
    """
    emi_paise = calculate_monthly_emi(
        principal_paise=payload.principal_paise,
        annual_rate_bps=payload.annual_rate_bps,
        tenure_months=payload.tenure_months,
    )

    fee_paise, gst_paise, net_disb_paise = calculate_fee_and_gst(
        principal_paise=payload.principal_paise,
        fee_type=payload.fee_type,
        fee_value=payload.fee_value,
        gst_rate_bps=payload.gst_rate_bps,
    )

    schedule = generate_amortisation_schedule(
        principal_paise=payload.principal_paise,
        annual_rate_bps=payload.annual_rate_bps,
        tenure_months=payload.tenure_months,
        start_date=date.today(),
    )

    total_interest_paise = sum(item["interest_component_paise"] for item in schedule)
    total_repayable_paise = sum(item["emi_amount_paise"] for item in schedule)

    # APR computation
    cash_flows = [-float(net_disb_paise) / 100.0] + [float(item["emi_amount_paise"]) / 100.0 for item in schedule]
    apr_pct = calculate_irr_apr(cash_flows)

    # Format dates as strings for JSON serialization
    serialized_schedule = []
    for s in schedule:
        item = dict(s)
        item["due_date"] = s["due_date"].isoformat()
        serialized_schedule.append(item)

    return {
        "principal_paise": payload.principal_paise,
        "tenure_months": payload.tenure_months,
        "annual_nominal_interest_rate_bps": payload.annual_rate_bps,
        "monthly_emi_paise": emi_paise,
        "total_interest_paise": total_interest_paise,
        "processing_fee_paise": fee_paise,
        "gst_paise": gst_paise,
        "net_disbursement_paise": net_disb_paise,
        "total_repayable_paise": total_repayable_paise,
        "apr_percent": apr_pct,
        "schedule": serialized_schedule,
    }
