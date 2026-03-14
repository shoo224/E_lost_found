# config.py - Load settings from environment variables
# Used by the app to get MongoDB URI, JWT secret, AWS keys, etc.

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "elostfound"

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # OTP
    OTP_EXPIRE_MINUTES: int = 10

    # AWS
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET: str = "elost-found-uploads"

    # Email
    SES_FROM_EMAIL: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # CORS - list of allowed origins for frontend
    CORS_ORIGINS: str = "http://localhost:5500,http://127.0.0.1:5500"
    # Admin emails (comma-separated) - these users get admin role
    ADMIN_EMAILS: str = ""
    # Password for admin panel login (email + password, no OTP)
    ADMIN_PANEL_PASSWORD: str = ""
    API_BASE_URL: str = "http://localhost:8000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]

    @property
    def admin_emails_list(self) -> List[str]:
        return [x.strip().lower() for x in self.ADMIN_EMAILS.split(",") if x.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
