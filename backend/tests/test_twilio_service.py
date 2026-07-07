import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure backend path is included
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.twilio_service import send_sms, TwilioSMSClient

@pytest.mark.asyncio
async def test_send_sms_exception():
    # Mock os.getenv to simulate DEMO_MODE not being "true"
    with patch("backend.services.twilio_service.settings.DEMO_MODE", "false"):
        def getenv_side_effect(key, default=None):
            if key == "DEMO_MODE":
                return "false"
            return None


        # Mock the client object within the twilio_service module
        with patch("backend.services.twilio_service.client") as mock_client:
            # Set up the mock to raise an Exception when messages.create is called
            mock_client.messages.create.side_effect = Exception("Simulated Twilio Error")

            # Call send_sms
            result = await send_sms("1234567890", "Test Message")

            # Assert the function caught the exception and returned False
            assert result is False
