import uuid
from typing import Any, Dict


class MockBankVerificationProvider:
    """
    Deterministic simulated penny-drop bank account verification.
    """
    def verify_account(
        self,
        account_holder_name: str,
        bank_name: str,
        account_number: str,
        ifsc_code: str,
    ) -> Dict[str, Any]:
        req_id = str(uuid.uuid4())

        # Deterministic simulation rules:
        # If account number ends with 0000 -> INVALID_ACCOUNT
        # If account number ends with 1111 -> NAME_MISMATCH
        # Otherwise -> VERIFIED
        clean_acc = account_number.strip()

        if clean_acc.endswith("0000"):
            return {
                "provider_request_id": req_id,
                "status": "INVALID_ACCOUNT",
                "message": "Account does not exist or branch is invalid.",
                "penny_drop_reference": None,
            }
        elif clean_acc.endswith("1111"):
            return {
                "provider_request_id": req_id,
                "status": "NAME_MISMATCH",
                "message": f"Beneficiary name registered at bank does not match '{account_holder_name}'.",
                "penny_drop_reference": f"PND-{uuid.uuid4().hex[:8].upper()}",
            }
        else:
            return {
                "provider_request_id": req_id,
                "status": "VERIFIED",
                "message": "Bank account verified successfully via simulated penny-drop.",
                "penny_drop_reference": f"PND-{uuid.uuid4().hex[:8].upper()}",
            }


bank_provider = MockBankVerificationProvider()
