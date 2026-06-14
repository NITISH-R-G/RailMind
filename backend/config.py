import os
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str = Field(default="mongodb://localhost:27017/railmind")
    GEMINI_API_KEY: SecretStr = Field(default="mock_key")
    ANTHROPIC_API_KEY: SecretStr = Field(default="mock_key")
    TWILIO_ACCOUNT_SID: str = Field(default="mock_sid")
    TWILIO_AUTH_TOKEN: SecretStr = Field(default="mock_token")
    TWILIO_PHONE_NUMBER: str = Field(default="+1234567890")
    RAILWAYS_API_KEY: SecretStr = Field(default="mock_key")
    DEMO_MODE: bool = Field(default=True)
    OLLAMA_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="llama3")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
