from unittest.mock import AsyncMock

import pytest

from src.fastapi_email_auth.service import EmailAuthService
from src.fastapi_email_auth.storage.memory import (
    InMemoryCodeStorage,
    InMemoryUserStorage,
)


@pytest.mark.asyncio
async def test_full_auth_flow_auto_create_user():
    """Test authentication flow with user auto-creation enabled"""
    code_storage = InMemoryCodeStorage()
    user_storage = InMemoryUserStorage()

    service = EmailAuthService(
        code_storage=code_storage,
        user_storage=user_storage,
        smtp_host="localhost",
        smtp_port=587,
        smtp_user="test@test.com",
        smtp_password="password",
        jwt_secret="secret",
    )
    service._send_email = AsyncMock()

    email = "newuser@example.com"

    # Step 1: Send verification code
    await service.send_verification_code(email)

    # Step 2: Retrieve code
    code = await code_storage.get_code(email)
    assert code is not None

    # Step 3: This should create the user and return a token
    token = await service.verify_code(email, code, auto_create_user=True)
    assert isinstance(token, str)
    assert token

    # Step 4: User must now exist
    user = await user_storage.get_user(email)
    assert user is not None
    assert user["email"] == email
    assert user["last_login"] is not None

    # Step 5: Code must be deleted from storage
    assert await code_storage.get_code(email) is None


@pytest.mark.asyncio
async def test_full_auth_flow_without_auto_create_user_error():
    """Test authentication fails if user does not exist and auto-creation is disabled"""
    code_storage = InMemoryCodeStorage()
    user_storage = InMemoryUserStorage()

    service = EmailAuthService(
        code_storage=code_storage,
        user_storage=user_storage,
        smtp_host="localhost",
        smtp_port=587,
        smtp_user="test@test.com",
        smtp_password="password",
        jwt_secret="secret",
    )
    service._send_email = AsyncMock()

    email = "nouser@example.com"

    # Step 1: Send verification code
    await service.send_verification_code(email)
    code = await code_storage.get_code(email)
    assert code is not None

    # Step 2: Try to verify code - should fail because user does not exist
    with pytest.raises(ValueError, match="does not exist"):
        await service.verify_code(email, code, auto_create_user=False)

    # Step 3: User is still not present
    user = await user_storage.get_user(email)
    assert user is None


@pytest.mark.asyncio
async def test_full_auth_flow_existing_user():
    """Test authentication flow with existing user and auto-creation disabled"""
    code_storage = InMemoryCodeStorage()
    user_storage = InMemoryUserStorage()

    service = EmailAuthService(
        code_storage=code_storage,
        user_storage=user_storage,
        smtp_host="localhost",
        smtp_port=587,
        smtp_user="test@test.com",
        smtp_password="password",
        jwt_secret="secret",
    )
    service._send_email = AsyncMock()

    email = "existing@example.com"

    # Pre-create user (simulates registration or migration)
    await user_storage.get_or_create_user(email)

    # Step 1: Send verification code
    await service.send_verification_code(email)
    code = await code_storage.get_code(email)
    assert code is not None

    # Step 2: Verify code - should succeed for existing user
    token = await service.verify_code(email, code)
    assert isinstance(token, str)
    assert token

    # Step 3: User's last_login should be updated
    user = await user_storage.get_user(email)
    assert user is not None
    assert user["email"] == email
    assert user["last_login"] is not None

    # Step 4: Code should be deleted
    assert await code_storage.get_code(email) is None
