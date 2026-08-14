from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017/railmind"
    REDIS_URL: str = "redis://localhost:6379/0"

    # API Keys
    RAILWAYS_API_KEY: str = "mock_key"
    RAPIDAPI_KEY: str = "mock_key"
    GEMINI_API_KEY: str = "mock_key"
    ANTHROPIC_API_KEY: str = "mock_key"

    # Twilio Configuration
    TWILIO_ACCOUNT_SID: str = "mock_sid"
    TWILIO_AUTH_TOKEN: str = "mock_token"
    TWILIO_PHONE_NUMBER: str = "+1234567890"

    # Notification Phone Numbers
    MAINTENANCE_PHONE: str = "+1234567891"
    OPERATIONS_PHONE: str = "+1234567892"
    STATION_PHONE: str = "+1234567893"
    DEMO_PASSENGER_PHONE: str = "+1234567894"

    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "secret"

    # Local LLM Fallback (Ollama)
    OLLAMA_BASE_URL: str = "http://localhost:11434/api/generate"
    OLLAMA_MODEL: str = "llama3"

    # Demo Mode
    DEMO_MODE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
