import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    railways_api_key: str = Field(..., alias="RAILWAYS_API_KEY")
    rapidapi_key: str = Field(default="", alias="RAPIDAPI_KEY")
    twilio_account_sid: str = Field(..., alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(..., alias="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(..., alias="TWILIO_PHONE_NUMBER")
    demo_mode: str = Field(default="false", alias="DEMO_MODE")
    demo_passenger_phone: str = Field(default="", alias="DEMO_PASSENGER_PHONE")
    maintenance_phone: str = Field(..., alias="MAINTENANCE_PHONE")
    operations_phone: str = Field(..., alias="OPERATIONS_PHONE")
    station_phone: str = Field(..., alias="STATION_PHONE")
    ollama_fallback_url: str = Field(default="http://ollama:11434/api/generate", alias="OLLAMA_FALLBACK_URL")

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()
