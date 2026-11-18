from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List
from app.financial.ledger import create_balanced_journal_entry


def create_reversal_journal_entry(
    original_entry_reference: str,
    original_lines: List[Dict[str, Any]],
    reason: str = "Payment reversal compensation",
) -> Dict[str, Any]:
    """
    Creates an exact inverse compensating journal entry for a previously posted entry.
    All original Debits become Credits, and all original Credits become Debits.
    Ensures zero net impact on general ledger accounts.
    """
    debits = []
    credits = []

    for line in original_lines:
        if line["entry_direction"] == "CREDIT":
            # Original credit becomes a debit
            debits.append({
                "account_id": line["account_id"],
                "account_code": line.get("account_code"),
                "amount_paise": line["amount_paise"],
            })
        elif line["entry_direction"] == "DEBIT":
            # Original debit becomes a credit
            credits.append({
                "account_id": line["account_id"],
                "account_code": line.get("account_code"),
                "amount_paise": line["amount_paise"],
            })

    return create_balanced_journal_entry(
        entry_reference=f"REV-{original_entry_reference}",
        entry_type="REVERSAL",
        description=f"Compensating reversal for {original_entry_reference}: {reason}",
        debits=debits,
        credits=credits,
    )
