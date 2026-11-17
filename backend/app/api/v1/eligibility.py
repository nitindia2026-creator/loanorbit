from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.profile import CustomerProfile
from app.models.user import User

router = APIRouter(prefix="/eligibility", tags=["Eligibility Simulation"])


@router.get("/check")
async def evaluate_eligibility(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Simulated rule-based eligibility calculation engine.
    Calculates FOIR and indicative maximum loan limit based on verified income.
    """
    stmt = select(CustomerProfile).where(CustomerProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        return {
            "is_eligible": False,
            "max_eligible_amount_paise": 0,
            "reason": "Customer profile is incomplete. Please finish onboarding.",
            "risk_band": "HIGH_RISK",
            "rule_evaluation": {"profile_completed": False},
        }

    monthly_income = profile.monthly_income_paise
    monthly_expenses = profile.monthly_expenses_paise
    net_disposable = max(0, monthly_income - monthly_expenses)

    # Max monthly obligation allowed is 50% of disposable income
    max_monthly_emi = int(net_disposable * 0.5)

    # Indicative loan eligibility: approx 6x disposable monthly capacity, capped at ₹1,00,000 (10,000,000 paise)
    indicative_limit = min(10000000, max(1000000, max_monthly_emi * 6))

    is_eligible = monthly_income >= 1500000  # At least ₹15,000 monthly income

    risk_band = "LOW_RISK" if monthly_income >= 4000000 else "MEDIUM_RISK"

    return {
        "is_eligible": is_eligible,
        "max_eligible_amount_paise": indicative_limit if is_eligible else 0,
        "suggested_tenures_months": [3, 6, 12],
        "risk_band": risk_band,
        "reason": "Based on synthetic income-to-expense analysis (simulated).",
        "rule_evaluation": {
            "monthly_income_paise": monthly_income,
            "monthly_expenses_paise": monthly_expenses,
            "disposable_income_paise": net_disposable,
            "foir_percent": round((monthly_expenses / monthly_income) * 100, 1) if monthly_income > 0 else 100,
        },
        "disclaimer": "LOANORBIT DEMO — SIMULATED ELIGIBILITY NOT A CREDIT BUREAU DECISION",
    }
