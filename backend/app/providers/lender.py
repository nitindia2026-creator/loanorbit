import uuid
from typing import Any, Dict


class MockLenderProvider:
    """
    Deterministic simulated lender disbursement adapter.
    """
    def disburse(
        self,
        loan_reference: str,
        amount_paise: int,
        account_number: str,
        ifsc_code: str,
    ) -> Dict[str, Any]:
        req_id = str(uuid.uuid4())

        # If loan reference contains 'DISBFAIL', simulate failure
        if "DISBFAIL" in loan_reference:
            return {
                "provider_reference": f"LND-FAIL-{uuid.uuid4().hex[:8].upper()}",
                "status": "FAILED",
                "failure_reason": "Simulated partner lender liquidity or bank network timeout.",
            }

        return {
            "provider_reference": f"LND-TXN-{uuid.uuid4().hex[:10].upper()}",
            "status": "SUCCESS",
            "amount_disbursed_paise": amount_paise,
            "utr": f"UTR{uuid.uuid4().hex[:12].upper()}",
        }


lender_provider = MockLenderProvider()
