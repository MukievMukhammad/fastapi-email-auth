from unittest.mock import AsyncMock

import pytest

from src.fastapi_email_auth.service import EmailAuthService
from src.fastapi_email_auth.storage.memory import (
    InMemoryCodeStorage,
    InMemoryUserStorage,
)


@pytest.fixture
def auth_service():
    """Fixture for authentication service with mocked SMTP

    Creates a service instance with in-memory storage and mocked
    email sending functionality for testing without actual email delivery.
    """
    code_storage = InMemoryCodeStorage()
    user_storage = InMemoryUserStorage()

    service = EmailAuthService(
        code_storage=code_storage,
        user_storage=user_storage,
        smtp_host="localhost",
        smtp_port=587,
        smtp_user="test@test.com",
        smtp_password="password",
        jwt_secret="test-secret",
        word_count=2,
        code_ttl=600,
        max_attempts=5,
    )

    # Mock email sending to avoid actual SMTP connection
    service._send_email = AsyncMock()

    return service


@pytest.mark.asyncio
async def test_send_verification_code(auth_service):
    """Test sending verification code to user email"""
    email = "test@example.com"

    result = await auth_service.send_verification_code(email)

    # Verify TTL is returned correctly
    assert result["expires_in"] == 600

    # Verify email was sent
    assert auth_service._send_email.called


@pytest.mark.asyncio
async def test_send_code_custom_word_count(auth_service):
    """Test sending code with custom number of words"""
    email = "test@example.com"

    # Request code with 4 words instead of default 2
    await auth_service.send_verification_code(email, word_count=4)

    # Verify generated code has 4 words
    code = await auth_service.code_storage.get_code(email)
    assert len(code.split()) == 4


@pytest.mark.asyncio
async def test_verify_correct_code(auth_service):
    """Test successful code verification returns JWT token"""
    email = "test@example.com"

    # Step 1: Send verification code
    await auth_service.send_verification_code(email)
    code = await auth_service.code_storage.get_code(email)

    # Step 2: Verify code
    token = await auth_service.verify_code(email, code)

    # Verify token is generated
    assert token is not None
    assert isinstance(token, str)


@pytest.mark.asyncio
async def test_verify_incorrect_code(auth_service):
    """Test that incorrect code raises validation error"""
    email = "test@example.com"

    await auth_service.send_verification_code(email)

    # Verify wrong code raises error
    with pytest.raises(ValueError, match="Invalid code"):
        await auth_service.verify_code(email, "wrong code")


@pytest.mark.asyncio
async def test_verify_max_attempts_exceeded(auth_service):
    """Test that exceeding max attempts locks verification"""
    email = "test@example.com"

    await auth_service.send_verification_code(email)

    # Make 5 failed attempts (configured max_attempts)
    for _ in range(5):
        try:
            await auth_service.verify_code(email, "wrong code")
        except ValueError:
            pass

    # 6th attempt should raise max attempts exceeded error
    with pytest.raises(ValueError, match="Maximum verification attempts exceeded"):
        await auth_service.verify_code(email, "wrong code")
