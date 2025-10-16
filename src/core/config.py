from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "Water Flow Prediction API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_NAME: str = os.getenv('DB_NAME', 'water_flow_db')
    DB_USERNAME: str = os.getenv('DB_USERNAME', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'postgres')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'WaterFlowSecretKey')
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    CORS_ORIGINS: list = ["*"]
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
