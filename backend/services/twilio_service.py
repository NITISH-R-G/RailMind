from twilio.rest import Client # type: ignore
import os
import asyncio
from typing import Optional
from ..circuit_breaker import CircuitBreaker
from ..monitoring import TWILIO_API_STATUS
from ..config import settings

account_sid = settings.TWILIO_ACCOUNT_SID
auth_token = settings.TWILIO_AUTH_TOKEN.get_secret_value() if hasattr(settings.TWILIO_AUTH_TOKEN, 'get_secret_value') else settings.TWILIO_AUTH_TOKEN
from_number = settings.TWILIO_PHONE_NUMBER

twilio_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

# Initialize Twilio Client
try:
    if account_sid and auth_token:
        client = Client(account_sid, auth_token)
    else:
        client = None
except Exception as e:
    print(f"[RAILMIND] Twilio client initialization failed: {e}")
    client = None

@twilio_circuit_breaker
async def _send_sms_internal(client_instance, to: str, message: str, from_number: str):
    return await asyncio.to_thread(
        client_instance.messages.create,
        body=message[:160],
        from_=from_number,
        to=to
    )

async def send_sms(to: str, message: str) -> bool:
    # Check DEMO_MODE to bypass real SMS charges
    if os.getenv("DEMO_MODE") == "true":
        print(f"[DEMO SMS ALERT] Bypassed sending to {to}: {message}")
        return True
    try:
        if client:
            msg = await _send_sms_internal(client, to, message, from_number)
            print(f"[RAILMIND] SMS sent to {to}: {msg.sid}")
            TWILIO_API_STATUS.labels(status='success').inc()
            return True
        else:
            print(f"[RAILMIND] Twilio Client not configured. Skipped sending message to {to}: {message}")
            return False
    except Exception as e:
        print(f"[RAILMIND] SMS failed: {e}")
        TWILIO_API_STATUS.labels(status='failure').inc()
        return False

async def send_department_alerts(department_tasks: list) -> list:
    sent = []
    dept_phones = {
        "maintenance": os.getenv("MAINTENANCE_PHONE"),
        "operations": os.getenv("OPERATIONS_PHONE"),
        "station_manager": os.getenv("STATION_PHONE")
    }
    for task in department_tasks:
        phone = dept_phones.get(task["department"])
        if phone:
            message = f"[RailMind] {task['department'].upper()}: {task['task_description'][:100]} | Urgency: {task['urgency']}"
            success = await send_sms(phone, message)
            if success:
                sent.append(f"{task['department']} -> {phone}")
    
    passenger_sms = f"[RailMind Alert] Train delay detected. Please check platform boards for updates."
    await send_sms(os.getenv("DEMO_PASSENGER_PHONE"), passenger_sms)
    
    return sent

class TwilioSMSClient:
    def __init__(self, account_sid: str = None, auth_token: str = None, from_number: str = None):
        self.account_sid = account_sid or settings.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or (settings.TWILIO_AUTH_TOKEN.get_secret_value() if hasattr(settings.TWILIO_AUTH_TOKEN, 'get_secret_value') else settings.TWILIO_AUTH_TOKEN)
        self.from_number = from_number or settings.TWILIO_PHONE_NUMBER
        try:
            if self.account_sid and self.auth_token:
                self.client = Client(self.account_sid, self.auth_token)
            else:
                self.client = None
        except Exception:
            self.client = None

    async def send_incident_alert(self, to_number: str, message_body: str) -> Optional[str]:
        if os.getenv("DEMO_MODE") == "true":
            print(f"[DEMO SMS CLIENT] Bypassed sending to {to_number}: {message_body}")
            return "SMdemo1234567890abcdef"
        try:
            if self.client:
                msg = await _send_sms_internal(self.client, to_number, message_body, self.from_number)
                print(f"[RAILMIND] SMS sent via TwilioSMSClient to {to_number}: {msg.sid}")
                TWILIO_API_STATUS.labels(status='success').inc()
                return msg.sid
            else:
                print(f"[RAILMIND] TwilioSMSClient not configured. Skipped sending message to {to_number}: {message_body}")
                return None
        except Exception as e:
            print(f"[RAILMIND] TwilioSMSClient send failed: {e}")
            TWILIO_API_STATUS.labels(status='failure').inc()
            raise e
