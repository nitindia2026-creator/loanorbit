import logging
import uuid
from typing import Any, Dict

logger = logging.getLogger("loanorbit.notifications")


class MockNotificationProvider:
    """
    Simulated SMS & Email notification dispatcher.
    Logs all synthetic dispatches cleanly without calling external services.
    """
    def send_sms(self, mobile_number: str, text: str) -> Dict[str, Any]:
        msg_id = str(uuid.uuid4())
        logger.info(f"[SIMULATED SMS] To: {mobile_number} | Msg: {text}")
        return {
            "id": msg_id,
            "channel": "MOCK_SMS",
            "recipient": mobile_number,
            "status": "DELIVERED",
        }

    def send_email(self, email: str, subject: str, body: str) -> Dict[str, Any]:
        msg_id = str(uuid.uuid4())
        logger.info(f"[SIMULATED EMAIL] To: {email} | Sub: {subject}")
        return {
            "id": msg_id,
            "channel": "MOCK_EMAIL",
            "recipient": email,
            "status": "DELIVERED",
        }


notification_provider = MockNotificationProvider()
