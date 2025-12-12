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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    s = Settings()

    if not s.SECRET_KEY or s.SECRET_KEY == "WaterFlowPredictionSecretKey":
        if os.getenv("ENV", "development") != "development":
            raise RuntimeError("SECRET_KEY is not set or is insecure. Set SECRET_KEY in environment.")

    return s


settings: Settings = get_settings()