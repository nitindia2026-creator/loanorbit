from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List
from app.financial.emi import calculate_monthly_emi


def generate_amortisation_schedule(
    principal_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
    start_date: date,
) -> List[Dict[str, Any]]:
    """
    Generates exact reducing-balance repayment schedule in integer paise.
    Absorbs any minor rounding residual into the final instalment so that:
    - sum(principal_components) == principal_paise
    - final closing_principal == 0
    """
    emi_paise = calculate_monthly_emi(principal_paise, annual_rate_bps, tenure_months)
    annual_rate = Decimal(annual_rate_bps) / Decimal(10000)
    monthly_r = annual_rate / Decimal(12)

    schedule = []
    opening_principal = principal_paise

    for k in range(1, tenure_months + 1):
        due_date = start_date + relativedelta(months=k)

        # Calculate monthly interest component in paise
        interest_decimal = (Decimal(opening_principal) * monthly_r).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        interest_paise = int(interest_decimal)

        if k < tenure_months:
            principal_paise_k = emi_paise - interest_paise
            closing_principal = opening_principal - principal_paise_k
            actual_emi = emi_paise
        else:
            # Final period: principal clears remaining balance exactly
            principal_paise_k = opening_principal
            actual_emi = principal_paise_k + interest_paise
            closing_principal = 0

        schedule.append({
            "instalment_number": k,
            "due_date": due_date,
            "opening_principal_paise": opening_principal,
            "emi_amount_paise": actual_emi,
            "principal_component_paise": principal_paise_k,
            "interest_component_paise": interest_paise,
            "closing_principal_paise": closing_principal,
            "outstanding_amount_paise": actual_emi,
            "status": "SCHEDULED",
        })

        opening_principal = closing_principal

    return schedule
