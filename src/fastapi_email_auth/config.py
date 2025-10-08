"""Configuration settings for email authentication"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings

from .utils.bip39 import Language


class EmailAuthSettings(BaseSettings):
    """Configuration for email authentication service

    Load settings from environment variables or .env file.
    """

    # SMTP Configuration
    smtp_host: str = Field(default="localhost", description="SMTP server hostname")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_user: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP connection")
    smtp_from_email: Optional[str] = Field(
        default=None, description="From email address (defaults to smtp_user)"
    )

    allow_register_new_users: bool = Field(
        default=True, description="Allow create new user if not exists"
    )

    # JWT Configuration
    jwt_secret: str = Field(
        default="change-this-secret-key", description="Secret key for JWT token signing"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_expiry_days: int = Field(default=7, description="JWT token validity in days")

    # Code Generation
    code_word_count: int = Field(
        default=2,
        ge=1,
        le=12,
        description="Number of BIP-39 words in verification code",
    )
    code_language: Language = Field(
        default="english", description="Language for BIP-39 words"
    )
    code_separator: str = Field(default=" ", description="Separator between words")
    code_ttl: int = Field(
        default=600, ge=60, description="Code time-to-live in seconds"
    )

    # Security
    max_attempts: int = Field(
        default=3, ge=1, description="Maximum verification attempts"
    )
    rate_limit_window: int = Field(
        default=60, description="Rate limit window in seconds"
    )

    # Redis Configuration (optional)
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL (e.g., redis://localhost:6379/0)",
    )
    redis_key_prefix: str = Field(
        default="email_auth:", description="Prefix for Redis keys"
    )

    # Database Configuration (optional)
    database_url: Optional[str] = Field(
        default=None, description="Database connection URL"
    )

    model_config = {
        "env_prefix": "EMAIL_AUTH_",
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
        "env_ignore_empty": True,
    }

    @property
    def from_email(self) -> str:
        """Get from email address"""
        return self.smtp_from_email or self.smtp_user
