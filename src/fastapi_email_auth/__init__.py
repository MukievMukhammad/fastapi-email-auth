"""
FastAPI Email Authentication Package

Passwordless authentication via email verification codes.
"""

__version__ = "0.1.0"

from .dependencies import get_auth_service, get_current_user
from .models import (
    AuthResponse,
    EmailLoginRequest,
    TokenResponse,
    VerifyCodeRequest,
)
from .routes import router
from .service import EmailAuthService
from .utils.bip39 import BIP39Generator, generate_code, validate_code

__all__ = [
    # Models
    "EmailLoginRequest",
    "VerifyCodeRequest",
    "AuthResponse",
    "TokenResponse",
    # Service
    "EmailAuthService",
    "router",
    # Dependencies
    "get_auth_service",
    "get_current_user",
    "set_custom_service",
    # Utilities
    "BIP39Generator",
    "generate_code",
    "validate_code",
]
