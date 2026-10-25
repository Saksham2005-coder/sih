import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "ReguFlow 360"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = "supersecret_dev_key_change_in_production_reguflow360"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"
    
    # Demonstration & Persona Switcher Control
    DEMO_MODE: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./reguflow.db"
    
    # Uploads & Storage
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    
    # Timezone & Localization
    TIMEZONE: str = "Asia/Kolkata"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Optional AI Case Brief Assistant
    GEMINI_API_KEY: str = ""

    @property
    def is_demo_allowed(self) -> bool:
        """
        Fail closed: Demo features (such as persona listing and one-click login)
        are strictly prohibited in production mode even if DEMO_MODE was set to True.
        """
        if self.ENVIRONMENT.lower() == "production":
            return False
        return self.DEMO_MODE

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
