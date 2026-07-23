from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # MongoDB Config
    MONGODB_URI: str = "mongodb://localhost:27017/railmind"

    # API Keys
    RAILWAYS_API_KEY: str = "mock_key"
    RAPIDAPI_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = "mock_key"

    # Twilio Config
    TWILIO_ACCOUNT_SID: str = "mock_sid"
    TWILIO_AUTH_TOKEN: str = "mock_token"
    TWILIO_PHONE_NUMBER: str = "+1234567890"

    # Contact Numbers
    MAINTENANCE_PHONE: str = "+1234567891"
    OPERATIONS_PHONE: str = "+1234567892"
    STATION_PHONE: str = "+1234567893"
    DEMO_PASSENGER_PHONE: str = "+1234567894"
    COORDINATOR_PHONE_NUMBER: str = "+1234567891"

    # Admin Auth
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
