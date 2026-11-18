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
    cash_flows[0] = -net_disbursement (outflow from lender / inflow to borrower, must be negative)
    cash_flows[1..n] = +emi_amount (inflows to lender / repayments from borrower, must have at least one positive)
    """
    if len(cash_flows) < 2:
        raise ValueError("Cash flows must contain at least an initial disbursement and one repayment.")
    if cash_flows[0] >= 0:
        raise ValueError("Initial cash flow (disbursement) must be negative.")
    if not any(cf > 0 for cf in cash_flows[1:]):
        raise ValueError("Cash flows must contain at least one positive repayment inflow.")

    rate = guess
    converged = False

    for _ in range(max_iterations):
        npv = 0.0
        d_npv = 0.0
        for t, cf in enumerate(cash_flows):
            denom = (1.0 + rate) ** t
            npv += cf / denom
            if t > 0:
                d_npv -= t * cf / ((1.0 + rate) ** (t + 1))

        if abs(npv) < tolerance:
            converged = True
            break

        if abs(d_npv) < 1e-12:
            break

        new_rate = rate - (npv / d_npv)
        if new_rate <= -1.0:  # Prevent domain errors
            rate = rate / 2.0
        else:
            rate = new_rate

    if not converged and abs(npv) >= 1e-3:
        raise ValueError("APR calculation failed to converge numerically for given cash flows.")

    # Annualize monthly rate: APR = monthly_rate * 12 * 100
    return round(rate * 12.0 * 100.0, 2)
