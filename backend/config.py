from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017/railmind"
    admin_username: str = "admin"
    admin_password: str = "admin_pass_123"
    anthropic_api_key: str = "mock_key"
    gemini_api_key: str = "mock_key"
    twilio_account_sid: str = "mock_sid"
    twilio_auth_token: str = "mock_token"
    railways_api_key: str = "mock_key"
    redis_host: str = "localhost"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
