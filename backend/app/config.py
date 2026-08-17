from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./lottery.db"
    jwt_secret_key: str = "development-only-change-this-secret"
    access_minutes: int = 30
    refresh_days: int = 30
    webhook_secret: str = "development-webhook-secret"
    upi_payee_id: str = "merchant@upi"
    upi_payee_name: str = "DhanLaxmi"
    cors_origins: str = "http://localhost:8000,http://localhost:4173,http://127.0.0.1:4173"
    enable_docs: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
