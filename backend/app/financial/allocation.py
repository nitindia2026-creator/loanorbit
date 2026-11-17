from typing import Any, Dict, List, Tuple


def allocate_payment_waterfall(
    payment_amount_paise: int,
    instalments: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Applies payment amount against instalments using the configured priority waterfall:
    1. Due Charges / Penalties
    2. Due Interest
    3. Due Principal
    4. Surplus / Advance

    Returns:
    (list_of_allocations, unallocated_excess_paise)
    """
    remaining_payment = payment_amount_paise
    allocations = []

    for inst in instalments:
        if remaining_payment <= 0:
            break

        # Calculate pending interest and principal on this instalment
        pending_interest = max(0, inst["interest_component_paise"] - inst.get("paid_interest_paise", 0))
        pending_principal = max(0, inst["principal_component_paise"] - inst.get("paid_principal_paise", 0))
        pending_charges = inst.get("charges_paise", 0)

        # 1. Allocate to charges
        alloc_charges = min(remaining_payment, pending_charges)
        remaining_payment -= alloc_charges

        # 2. Allocate to interest
        alloc_interest = min(remaining_payment, pending_interest)
        remaining_payment -= alloc_interest

        # 3. Allocate to principal
        alloc_principal = min(remaining_payment, pending_principal)
        remaining_payment -= alloc_principal

        if alloc_charges > 0 or alloc_interest > 0 or alloc_principal > 0:
            allocations.append({
                "instalment_id": inst["id"],
                "instalment_number": inst["instalment_number"],
                "allocated_charges_paise": alloc_charges,
                "allocated_interest_paise": alloc_interest,
                "allocated_principal_paise": alloc_principal,
                "total_allocated_paise": alloc_charges + alloc_interest + alloc_principal,
            })

    return allocations, remaining_payment
