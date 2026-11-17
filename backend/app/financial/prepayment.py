from typing import Dict


def calculate_foreclosure_quote(
    outstanding_principal_paise: int,
    accrued_interest_paise: int,
    outstanding_penalties_paise: int = 0,
    foreclosure_fee_paise: int = 0,
) -> Dict[str, int]:
    """
    Computes early foreclosure quotation for active loan.
    """
    total_settlement_paise = (
        outstanding_principal_paise
        + accrued_interest_paise
        + outstanding_penalties_paise
        + foreclosure_fee_paise
    )

    return {
        "outstanding_principal_paise": outstanding_principal_paise,
        "accrued_interest_paise": accrued_interest_paise,
        "outstanding_penalties_paise": outstanding_penalties_paise,
        "foreclosure_fee_paise": foreclosure_fee_paise,
        "total_settlement_paise": total_settlement_paise,
    }
