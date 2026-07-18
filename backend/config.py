from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017/railmind"
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    ANTHROPIC_API_KEY: str = "mock_key"
    GEMINI_API_KEY: str = "mock_key"
    TWILIO_ACCOUNT_SID: str = "mock_sid"
    TWILIO_AUTH_TOKEN: str = "mock_token"
    TWILIO_PHONE_NUMBER: str = "+1234567890"
    TWILIO_TEST_PHONE: str = ""
    RAILWAYS_API_KEY: str = "mock_key"
    DEMO_MODE: str = "false"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "secret"
    MAINTENANCE_PHONE: str = "+919651058174"
    OPERATIONS_PHONE: str = "+919651058174"
    STATION_PHONE: str = "+919651058174"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
