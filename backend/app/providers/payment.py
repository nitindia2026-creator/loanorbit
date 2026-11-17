import uuid
from typing import Any, Dict


class MockPaymentProvider:
    """
    Deterministic simulated UPI payment gateway.
    Never connects to NPCI, real UPI, or merchant gateways.
    """
    def initiate_upi_payment(
        self,
        loan_id: str,
        amount_paise: int,
        scenario: str = "SUCCESS",
    ) -> Dict[str, Any]:
        txn_id = f"UPI-{uuid.uuid4().hex[:12].upper()}"

        upper_scenario = scenario.strip().upper()

        if upper_scenario == "FAILURE" or upper_scenario == "FAILED":
            return {
                "transaction_id": txn_id,
                "status": "FAILED",
                "failure_reason": "Simulated insufficient funds or bank server error.",
                "amount_paise": amount_paise,
            }
        elif upper_scenario == "PENDING":
            return {
                "transaction_id": txn_id,
                "status": "PENDING",
                "message": "Payment is awaiting confirmation from user bank.",
                "amount_paise": amount_paise,
            }
        else:
            return {
                "transaction_id": txn_id,
                "status": "SUCCESS",
                "provider_reference": f"NPCI-{uuid.uuid4().hex[:8].upper()}",
                "amount_paise": amount_paise,
            }


payment_provider = MockPaymentProvider()
