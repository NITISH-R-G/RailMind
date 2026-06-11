from twilio.rest import Client # type: ignore
import os
from typing import Optional

from backend.config import settings
from backend.utils.circuit_breaker import create_circuit_breaker
from backend.utils.metrics import TWILIO_RESPONSE_STATUS
from backend.utils.logger import get_json_logger

logger = get_json_logger(__name__)

account_sid = settings.twilio_account_sid
auth_token = settings.twilio_auth_token
from_number = settings.twilio_phone_number

twilio_circuit_breaker = create_circuit_breaker("twilio_api")

# Initialize Twilio Client
try:
    if account_sid and auth_token:
        client = Client(account_sid, auth_token)
    else:
        client = None
except Exception as e:
    logger.error(f"[RAILMIND] Twilio client initialization failed: {e}")
    client = None

@twilio_circuit_breaker
def execute_twilio_sms(client_obj, to: str, body: str, from_str: str):
    return client_obj.messages.create(
        body=body,
        from_=from_str,
        to=to
    )

async def send_sms(to: str, message: str) -> bool:
    # Check DEMO_MODE to bypass real SMS charges
    if settings.demo_mode == "true":
        logger.info(f"[DEMO SMS ALERT] Bypassed sending to {to}: {message}")
        TWILIO_RESPONSE_STATUS.labels(status="demo_bypassed").inc()
        return True
    try:
        if client:
            msg = execute_twilio_sms(client, to, message[:160], from_number)
            logger.info(f"[RAILMIND] SMS sent to {to}: {msg.sid}")
            TWILIO_RESPONSE_STATUS.labels(status="success").inc()
            return True
        else:
            logger.warning(f"[RAILMIND] Twilio Client not configured. Skipped sending message to {to}: {message}")
            TWILIO_RESPONSE_STATUS.labels(status="not_configured").inc()
            return False
    except Exception as e:
        logger.error(f"[RAILMIND] SMS failed/circuit open: {e}")
        TWILIO_RESPONSE_STATUS.labels(status="failure").inc()
        return False

async def send_department_alerts(department_tasks: list) -> list:
    sent = []
    dept_phones = {
        "maintenance": settings.maintenance_phone,
        "operations": settings.operations_phone,
        "station_manager": settings.station_phone
    }
    for task in department_tasks:
        phone = dept_phones.get(task["department"])
        if phone:
            message = f"[RailMind] {task['department'].upper()}: {task['task_description'][:100]} | Urgency: {task['urgency']}"
            success = await send_sms(phone, message)
            if success:
                sent.append(f"{task['department']} -> {phone}")
    
    passenger_sms = f"[RailMind Alert] Train delay detected. Please check platform boards for updates."
    if settings.demo_passenger_phone:
        await send_sms(settings.demo_passenger_phone, passenger_sms)
    
    return sent

class TwilioSMSClient:
    def __init__(self, account_sid: str = None, auth_token: str = None, from_number: str = None):
        self.account_sid = account_sid or settings.twilio_account_sid
        self.auth_token = auth_token or settings.twilio_auth_token
        self.from_number = from_number or settings.twilio_phone_number
        try:
            if self.account_sid and self.auth_token:
                self.client = Client(self.account_sid, self.auth_token)
            else:
                self.client = None
        except Exception:
            self.client = None

    async def send_incident_alert(self, to_number: str, message_body: str) -> Optional[str]:
        if settings.demo_mode == "true":
            logger.info(f"[DEMO SMS CLIENT] Bypassed sending to {to_number}: {message_body}")
            TWILIO_RESPONSE_STATUS.labels(status="demo_bypassed").inc()
            return "SMdemo1234567890abcdef"
        try:
            if self.client:
                msg = execute_twilio_sms(self.client, to_number, message_body[:160], self.from_number)
                logger.info(f"[RAILMIND] SMS sent via TwilioSMSClient to {to_number}: {msg.sid}")
                TWILIO_RESPONSE_STATUS.labels(status="success").inc()
                return msg.sid
            else:
                logger.warning(f"[RAILMIND] TwilioSMSClient not configured. Skipped sending message to {to_number}: {message_body}")
                TWILIO_RESPONSE_STATUS.labels(status="not_configured").inc()
                return None
        except Exception as e:
            logger.error(f"[RAILMIND] TwilioSMSClient send failed/circuit open: {e}")
            TWILIO_RESPONSE_STATUS.labels(status="failure").inc()
            raise e
