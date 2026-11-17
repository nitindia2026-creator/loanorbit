import random
import uuid
from typing import Dict
from app.core.config import settings


class MockOTPProvider:
    """
    Deterministic simulated OTP delivery provider for Sandbox demo.
    Never connects to real SMS gateways.
    """
    def __init__(self):
        # In-memory store for OTP simulation: mobile_number -> code
        self._cache: Dict[str, str] = {}

    def send_otp(self, mobile_number: str) -> Dict[str, str]:
        # Fixed deterministic code for test numbers, or configurable default
        if mobile_number.endswith("0000"):
            code = "999999"
        else:
            code = settings.MOCK_OTP_DEFAULT_CODE
            
        self._cache[mobile_number] = code
        return {
            "provider_request_id": str(uuid.uuid4()),
            "status": "DELIVERED_SIMULATED",
            "delivery_channel": "MOCK_SMS",
            "code": code,
        }

    def verify_otp(self, mobile_number: str, submitted_code: str) -> bool:
        expected = self._cache.get(mobile_number, settings.MOCK_OTP_DEFAULT_CODE)
        return submitted_code == expected or submitted_code == settings.MOCK_OTP_DEFAULT_CODE


otp_provider = MockOTPProvider()
