from typing import Any, Dict, List


def reconcile_loan_amortisation(
    outstanding_principal_paise: int,
    instalments: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Verifies that the loan's outstanding principal matches the sum of
    unpaid principal across all active instalments.
    """
    total_unpaid_principal = sum(
        max(0, inst["principal_component_paise"] - inst.get("paid_principal_paise", 0))
        for inst in instalments
    )

    is_balanced = outstanding_principal_paise == total_unpaid_principal
    variance_paise = abs(outstanding_principal_paise - total_unpaid_principal)

    return {
        "is_reconciled": is_balanced,
        "loan_outstanding_principal_paise": outstanding_principal_paise,
        "schedule_unpaid_principal_paise": total_unpaid_principal,
        "variance_paise": variance_paise,
    }


def reconcile_general_ledger_entries(
    journal_entries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validates that every journal entry in the system is individually balanced,
    and that global debits equal global credits.
    """
    unbalanced_entries = []
    total_debits = 0
    total_credits = 0

    for entry in journal_entries:
        entry_deb = sum(line["amount_paise"] for line in entry["lines"] if line["entry_direction"] == "DEBIT")
        entry_cred = sum(line["amount_paise"] for line in entry["lines"] if line["entry_direction"] == "CREDIT")

        total_debits += entry_deb
        total_credits += entry_cred

        if entry_deb != entry_cred:
            unbalanced_entries.append({
                "entry_reference": entry["entry_reference"],
                "debits": entry_deb,
                "credits": entry_cred,
                "variance": abs(entry_deb - entry_cred),
            })

    return {
        "is_ledger_balanced": len(unbalanced_entries) == 0 and total_debits == total_credits,
        "total_system_debits_paise": total_debits,
        "total_system_credits_paise": total_credits,
        "unbalanced_entry_count": len(unbalanced_entries),
        "unbalanced_entries": unbalanced_entries,
    }
