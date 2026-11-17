from decimal import Decimal
from typing import List


def calculate_irr_apr(
    cash_flows: List[float],
    guess: float = 0.02,
    tolerance: float = 1e-7,
    max_iterations: int = 100,
) -> float:
    """
    Computes annualized percentage rate (APR) from monthly cash flows via Newton-Raphson IRR solver.
    Cash flows format:
    cash_flows[0] = -net_disbursement (outflow from lender / inflow to borrower)
    cash_flows[1..n] = +emi_amount (inflows to lender / repayments from borrower)
    """
    if len(cash_flows) < 2 or cash_flows[0] >= 0:
        raise ValueError("Invalid cash flows for APR computation.")

    rate = guess
    for _ in range(max_iterations):
        npv = 0.0
        d_npv = 0.0
        for t, cf in enumerate(cash_flows):
            denom = (1.0 + rate) ** t
            npv += cf / denom
            if t > 0:
                d_npv -= t * cf / ((1.0 + rate) ** (t + 1))

        if abs(npv) < tolerance:
            # Annualize monthly rate: APR = monthly_rate * 12 * 100
            return round(rate * 12.0 * 100.0, 2)

        if abs(d_npv) < 1e-12:
            break

        rate = rate - (npv / d_npv)

    # Fallback approximation if Newton-Raphson does not converge
    return round(rate * 12.0 * 100.0, 2)
