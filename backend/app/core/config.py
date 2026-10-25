import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

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
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_demo_allowed(self) -> bool:
        """
        Fail closed: Demo features (such as persona listing and one-click login)
        are strictly prohibited in production mode even if DEMO_MODE was set to True.
        """
        if self.is_production:
            return False
        return self.DEMO_MODE

    @model_validator(mode="after")
    def validate_production_invariants(self) -> "Settings":
        """
        Production-safety invariant guards:
        When ENVIRONMENT=production, startup fails closed immediately if insecure
        development keys, debug mode, SQLite database, or demo settings are active.
        """
        if self.ENVIRONMENT.lower() == "production":
            # 1. SECRET_KEY validation
            if not self.SECRET_KEY or not self.SECRET_KEY.strip():
                raise ValueError(
                    "Production safety violation: SECRET_KEY must not be empty. "
                    "Supply a strong, cryptographically secure key (minimum 32 characters) via the SECRET_KEY environment variable."
                )

            insecure_key_patterns = [
                "supersecret_dev_key_change_in_production_reguflow360",
                "secret",
                "changeme",
                "development",
                "password",
                "insecure_default_secret_key_change_in_production",
                "reguflow360_secret_key_change_in_production",
                "dev_key",
                "change_in_production",
            ]
            key_lower = self.SECRET_KEY.lower()
            if any(p in key_lower for p in insecure_key_patterns):
                raise ValueError(
                    "Production safety violation: SECRET_KEY matches a known development default or insecure pattern. "
                    "A unique production secret key (minimum 32 characters) must be provided."
                )

            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    f"Production safety violation: SECRET_KEY is too short ({len(self.SECRET_KEY)} characters). "
                    "Production signing keys must be at least 32 characters long."
                )

            # 2. DEBUG mode check
            if self.DEBUG:
                raise ValueError(
                    "Production safety violation: DEBUG mode must be False in production."
                )

            # 3. DEMO_MODE check
            if self.DEMO_MODE:
                raise ValueError(
                    "Production safety violation: DEMO_MODE must be False in production. "
                    "Shared demo identities and mock authentications are prohibited."
                )

            # 4. DATABASE_URL validation
            db_url = self.DATABASE_URL.lower()
            if db_url.startswith("sqlite"):
                raise ValueError(
                    "Production safety violation: SQLite is prohibited in production. "
                    "Configure a resilient PostgreSQL connection string via DATABASE_URL."
                )

            insecure_db_passwords = ["reguflow_secret", "reguflow_secure_pass", ":postgres@", ":password@"]
            if any(p in db_url for p in insecure_db_passwords):
                raise ValueError(
                    "Production safety violation: DATABASE_URL contains known default development credentials. "
                    "Production deployments must use unique, securely provisioned credentials."
                )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
