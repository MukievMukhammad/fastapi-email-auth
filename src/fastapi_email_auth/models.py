"""Pydantic models for request/response validation"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class EmailLoginRequest(BaseModel):
    """Request model for email login (code sending)

    Attributes:
        email: User's email address (validated format)
    """

    email: EmailStr = Field(
        ..., description="User's email address", examples=["user@example.com"]
    )

    @field_validator("email", mode="before")
    @classmethod
    def strip_email(cls, value: str) -> str:
        """Trim whitespace from email but preserve case"""
        if isinstance(value, str):
            return value.strip()
        return value

    model_config = {"json_schema_extra": {"examples": [{"email": "user@example.com"}]}}


class VerifyCodeRequest(BaseModel):
    """Request model for code verification

    Attributes:
        email: User's email address
        code: Verification code received via email
    """

    email: EmailStr = Field(..., description="User's email address")
    code: str = Field(
        ...,
        min_length=1,
        description="Verification code (BIP-39 words)",
        examples=["abandon ability", "солнце-река"],
    )

    @field_validator("email", mode="before")
    @classmethod
    def strip_email(cls, value: str) -> str:
        """Trim whitespace from email"""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("code", mode="before")
    @classmethod
    def validate_code(cls, value: str) -> str:
        """Validate code is not empty after stripping"""
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Code cannot be empty")
        return value

    model_config = {
        "json_schema_extra": {
            "examples": [{"email": "user@example.com", "code": "abandon ability"}]
        }
    }


class AuthResponse(BaseModel):
    """Response model for authentication operations

    Attributes:
        success: Whether operation was successful
        message: Human-readable status message
        auth_request_id: Unique identifier for this auth request (optional)
        expires_in: Code validity duration in seconds (optional)
    """

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(
        ...,
        description="Human-readable message",
        examples=["Code sent successfully", "Rate limit exceeded"],
    )
    expires_in: Optional[int] = Field(
        None, description="Code expiration time in seconds", examples=[600]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Code sent successfully",
                    "auth_request_id": "abc123",
                    "expires_in": 600,
                },
                {"success": False, "message": "Rate limit exceeded"},
            ]
        }
    }


class TokenResponse(BaseModel):
    """Response model for successful authentication

    Attributes:
        access_token: JWT access token
        token_type: Token type (default: bearer)
    """

    access_token: str = Field(
        ...,
        min_length=1,
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(
        default="bearer", description="Token type for Authorization header"
    )

    @field_validator("access_token")
    @classmethod
    def validate_token(cls, value: str) -> str:
        """Ensure token is not empty"""
        if not value or not value.strip():
            raise ValueError("Access token cannot be empty")
        return value

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                }
            ]
        }
    }
