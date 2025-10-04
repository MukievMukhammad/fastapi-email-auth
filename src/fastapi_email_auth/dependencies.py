"""FastAPI dependencies with flexible configuration"""

from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import EmailAuthSettings
from .service import EmailAuthService
from .storage.factory import create_code_storage, create_user_storage

# Security scheme
security = HTTPBearer()

# Global instances
_settings: Optional[EmailAuthSettings] = None
_service: Optional[EmailAuthService] = None


@lru_cache()
def get_settings() -> EmailAuthSettings:
    """Get cached settings instance

    Loads from environment variables and .env file.
    Uses lru_cache to ensure singleton.
    """
    global _settings
    if _settings is None:
        _settings = EmailAuthSettings()
    return _settings


def create_service(settings: EmailAuthSettings) -> EmailAuthService:
    """Create service instance from settings

    Args:
        settings: Configuration settings

    Returns:
        Configured EmailAuthService instance
    """
    code_storage = create_code_storage(settings)
    user_storage = create_user_storage(settings)

    return EmailAuthService(
        code_storage=code_storage,
        user_storage=user_storage,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_password=settings.smtp_password,
        jwt_secret=settings.jwt_secret,
        jwt_algorithm=settings.jwt_algorithm,
        word_count=settings.code_word_count,
        code_language=settings.code_language,
        code_separator=settings.code_separator,
        code_ttl=settings.code_ttl,
        max_attempts=settings.max_attempts,
        jwt_expiry_days=settings.jwt_expiry_days,
    )


def get_auth_service(
    settings: EmailAuthSettings = Depends(get_settings),
) -> EmailAuthService:
    """Dependency to get authentication service

    Creates service based on configuration. Reuses instance if already created.

    Args:
        settings: Application settings from dependency

    Returns:
        Configured EmailAuthService instance
    """
    global _service

    if _service is None:
        _service = create_service(settings)

    return _service


def set_custom_service(service: EmailAuthService) -> None:
    """Override service with custom instance

    Useful for testing or custom initialization.

    Args:
        service: Custom service instance
    """
    global _service
    _service = service


def set_custom_settings(settings: EmailAuthSettings) -> None:
    """Override settings with custom instance

    Args:
        settings: Custom settings instance
    """
    global _settings
    _settings = settings


def reset_dependencies() -> None:
    """Reset all cached dependencies (for testing)"""
    global _service, _settings
    _service = None
    _settings = None
    get_settings.cache_clear()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: EmailAuthService = Depends(get_auth_service),
) -> str:
    """Get current authenticated user from JWT token"""
    try:
        token = credentials.credentials
        email = service.decode_token(token)
        return email
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
