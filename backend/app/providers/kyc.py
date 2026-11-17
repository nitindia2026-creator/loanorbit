import uuid
from typing import Any, Dict


class MockKYCProvider:
    """
    Deterministic simulated KYC verification adapter.
    Never connects to government or real bureau databases.
    """
    def verify_document(self, id_type: str, id_number: str) -> Dict[str, Any]:
        req_id = str(uuid.uuid4())

        # Deterministic simulation rules:
        # If ID ends with 'FAIL', simulate REJECTED
        # If ID ends with 'REV', simulate MANUAL_REVIEW
        # Otherwise, simulate VERIFIED
        upper_id = id_number.strip().upper()

        if upper_id.endswith("FAIL") or upper_id.endswith("REJ"):
            return {
                "provider_request_id": req_id,
                "status": "REJECTED",
                "reason_code": "DOC_BLURRED_OR_INVALID",
                "message": "Uploaded synthetic document is unreadable or forged.",
            }
        elif upper_id.endswith("REV"):
            return {
                "provider_request_id": req_id,
                "status": "MANUAL_REVIEW",
                "reason_code": "OFFICER_VERIFICATION_REQUIRED",
                "message": "Flagged for manual review by KYC officer.",
            }
        else:
            return {
                "provider_request_id": req_id,
                "status": "VERIFIED",
                "name_matched": True,
                "message": "Synthetic document successfully verified.",
            }


kyc_provider = MockKYCProvider()
