from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple


def paise_to_rupees(paise: int) -> Decimal:
    """Converts integer paise to exact Decimal rupees."""
    return (Decimal(paise) / Decimal(100)).quantize(Decimal("0.01"))


def rupees_to_paise(rupees: Decimal) -> int:
    """Converts Decimal rupees to integer paise with standard rounding."""
    return int((rupees * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calculate_monthly_emi(
    principal_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
) -> int:
    """
    Computes monthly reducing balance EMI in integer paise.
    
    Formula:
    EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
    
    Where:
    P = Principal in rupees (Decimal)
    r = Monthly interest rate = (annual_rate_bps / 10000) / 12
    n = tenure_months
    """
    if principal_paise <= 0:
        raise ValueError("Principal must be strictly positive.")
    if tenure_months <= 0:
        raise ValueError("Tenure months must be strictly positive.")

    # Convert principal to Decimal
    p = Decimal(principal_paise) / Decimal(100)

    # Zero interest special case
    if annual_rate_bps == 0:
        emi_rupees = (p / Decimal(tenure_months)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return rupees_to_paise(emi_rupees)

    # Monthly interest rate
    annual_rate = Decimal(annual_rate_bps) / Decimal(10000)
    r = annual_rate / Decimal(12)

    # (1 + r)^n
    one_plus_r_n = (Decimal(1) + r) ** tenure_months

    # EMI calculation
    numerator = p * r * one_plus_r_n
    denominator = one_plus_r_n - Decimal(1)

    emi_rupees = (numerator / denominator).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return rupees_to_paise(emi_rupees)


def calculate_fee_and_gst(
    principal_paise: int,
    fee_type: str,
    fee_value: int,
    gst_rate_bps: int = 1800,
) -> Tuple[int, int, int]:
    """
    Calculates processing fee, applicable GST, and net disbursement in paise.
    Returns: (processing_fee_paise, gst_paise, net_disbursement_paise)
    """
    if fee_type.upper() == "FIXED":
        fee_paise = fee_value
    elif fee_type.upper() == "PERCENTAGE":
        # fee_value is in basis points, e.g. 200 = 2%
        fee_rupees = (Decimal(principal_paise) * Decimal(fee_value) / Decimal(1000000)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        fee_paise = int(fee_rupees * Decimal(100))
    else:
        fee_paise = 0

    # GST on fee only
    gst_rupees = (Decimal(fee_paise) * Decimal(gst_rate_bps) / Decimal(1000000)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    gst_paise = int(gst_rupees * Decimal(100))

    net_disbursement_paise = principal_paise - (fee_paise + gst_paise)
    return fee_paise, gst_paise, net_disbursement_paise
