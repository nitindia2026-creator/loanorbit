import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List


def create_balanced_journal_entry(
    entry_reference: str,
    entry_type: str,
    description: str,
    debits: List[Dict[str, Any]],
    credits: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validates and formats a double-entry general ledger journal entry.
    Strictly asserts that:
    sum(debits[].amount_paise) == sum(credits[].amount_paise)
    """
    total_debits = sum(d["amount_paise"] for d in debits)
    total_credits = sum(c["amount_paise"] for c in credits)

    if total_debits != total_credits:
        raise ValueError(
            f"Unbalanced journal entry: Debits ({total_debits} paise) != Credits ({total_credits} paise)."
        )

    lines = []
    for d in debits:
        lines.append({
            "account_id": d["account_id"],
            "account_code": d.get("account_code"),
            "entry_direction": "DEBIT",
            "amount_paise": d["amount_paise"],
        })
    for c in credits:
        lines.append({
            "account_id": c["account_id"],
            "account_code": c.get("account_code"),
            "entry_direction": "CREDIT",
            "amount_paise": c["amount_paise"],
        })

    return {
        "id": str(uuid.uuid4()),
        "entry_reference": entry_reference,
        "entry_type": entry_type,
        "description": description,
        "posted_at": datetime.now(timezone.utc),
        "total_amount_paise": total_debits,
        "lines": lines,
    }
