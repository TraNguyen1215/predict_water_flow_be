from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os
from typing import Any


class Settings(BaseSettings):
    PROJECT_NAME: str = "Water Flow Prediction API"
    API_V1_STR: str = "/api/v1"

    # JWT / security settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days by default

    # SMTP settings for email and SMS
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "" # Your SMTP username/email
    SMTP_PASSWORD: str = "" # Your SMTP password
    SENDER_EMAIL: str = "" # Your sender email address
    
    # SMS gateway (using email-to-SMS gateway)
    # For Vietnam carriers (if they support email-to-SMS):
    # - Viettel: {phone}@sms.viettel.vn
    # - Vinaphone: {phone}@sms.vinaphone.vn
    # - MobiFone: {phone}@sms.mobifone.vn
    # Note: Most Vietnamese carriers use API-based SMS instead of email-to-SMS
    SMS_GATEWAY_EMAIL: str = "{phone}@sms.viettel.vn"  # Default to Viettel for Vietnam
    SEND_SMS: bool = True  # Enable/disable SMS sending

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    s = Settings()

    if not s.SECRET_KEY or s.SECRET_KEY == "WaterFlowPredictionSecretKey":
        if os.getenv("ENV", "development") != "development":
            raise RuntimeError("SECRET_KEY is not set or is insecure. Set SECRET_KEY in environment.")

    return s


settings: Settings = get_settings()