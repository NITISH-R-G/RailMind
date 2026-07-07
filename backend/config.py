from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    MONGODB_URI: str
    GEMINI_API_KEY: str
    ANTHROPIC_API_KEY: str

    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str

    DEMO_MODE: str = "false"

    RAPIDAPI_KEY: Optional[str] = None
    RAPIDAPI_HOST: Optional[str] = "irctc1.p.rapidapi.com"
    RAILWAYS_API_KEY: Optional[str] = None

    MAINTENANCE_PHONE: str
    OPERATIONS_PHONE: str
    STATION_PHONE: str
    DEMO_PASSENGER_PHONE: Optional[str] = None

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
