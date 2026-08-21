from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "BondGuard Pro"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/bondguard"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    ENVIRONMENT: str = "development"
    FRED_API_KEY: str = ""
    
    # Security & JWT settings
    JWT_SECRET_KEY: str = "DEV_SECRET_DO_NOT_USE_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if self.JWT_SECRET_KEY == "DEV_SECRET_DO_NOT_USE_IN_PRODUCTION":
                raise ValueError("JWT_SECRET_KEY must be overridden with a secure value in production environments.")
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
