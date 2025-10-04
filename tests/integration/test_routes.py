"""Integration tests for FastAPI routes"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.fastapi_email_auth.routes import router
from src.fastapi_email_auth.service import EmailAuthService
from src.fastapi_email_auth.storage.memory import (
    InMemoryCodeStorage,
    InMemoryUserStorage,
)


@pytest.fixture
def app():
    """Create FastAPI test application"""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/auth")
    return test_app


@pytest.fixture
def client(app):
    """Create test client for API requests"""
    return TestClient(app)


@pytest.fixture
def mock_service():
    """Create mocked authentication service"""
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
    )

    service._send_email = AsyncMock()
    return service


# POST /auth/send-code Tests


def test_send_code_success(client, mock_service):
    """Test successful verification code sending"""
    with patch(
        "src.fastapi_email_auth.dependencies.get_auth_service",
        return_value=mock_service,
    ):
        response = client.post("/auth/send-code", json={"email": "test@example.com"})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "expires_in" in data


def test_send_code_invalid_email(client):
    """Test send code with invalid email format"""
    response = client.post("/auth/send-code", json={"email": "not-an-email"})

    # FastAPI returns 422 for validation errors
    assert response.status_code == 422


def test_send_code_missing_email(client):
    """Test send code without email field"""
    response = client.post("/auth/send-code", json={})

    assert response.status_code == 422


def test_send_code_rate_limited(client, mock_service):
    """Test rate limiting on code requests"""
    with patch(
        "src.fastapi_email_auth.dependencies.get_auth_service",
        return_value=mock_service,
    ):
        email = "test@example.com"

        # First request succeeds
        response1 = client.post("/auth/send-code", json={"email": email})
        assert response1.status_code == 200

        # Mock rate limit error
        async def rate_limited(*args, **kwargs):
            raise ValueError("Rate limit exceeded")

        mock_service.send_verification_code = rate_limited

        # Second request is rate limited
        response2 = client.post("/auth/send-code", json={"email": email})
        assert response2.status_code == 429 or response2.status_code == 400


# POST /auth/verify Tests


def test_verify_code_success(client, mock_service):
    """Test successful code verification returns token"""
    with patch(
        "src.fastapi_email_auth.dependencies.get_auth_service",
        return_value=mock_service,
    ):
        email = "existing@example.com"

        # Pre-create user
        import asyncio

        asyncio.run(mock_service.user_storage.get_or_create_user(email))

        # Send code
        client.post("/auth/send-code", json={"email": email})

        # Get code from storage
        code = asyncio.run(mock_service.code_storage.get_code(email))

        # Verify code
        response = client.post("/auth/verify", json={"email": email, "code": code})

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_verify_code_incorrect(client, mock_service):
    """Test verification with incorrect code"""
    with patch(
        "src.fastapi_email_auth.dependencies.get_auth_service",
        return_value=mock_service,
    ):
        email = "test@example.com"

        # Send code first
        client.post("/auth/send-code", json={"email": email})

        # Try wrong code
        response = client.post(
            "/auth/verify", json={"email": email, "code": "wrong code"}
        )

    assert response.status_code == 400


def test_verify_code_missing_fields(client):
    """Test verification with missing fields"""
    # Missing code
    response = client.post("/auth/verify", json={"email": "test@example.com"})
    assert response.status_code == 422

    # Missing email
    response = client.post("/auth/verify", json={"code": "some code"})
    assert response.status_code == 422


def test_verify_code_user_not_exists(client, mock_service):
    """Test verification fails for non-existent user"""
    with patch(
        "src.fastapi_email_auth.dependencies.get_auth_service",
        return_value=mock_service,
    ):
        email = "nouser@example.com"

        # Send code
        client.post("/auth/send-code", json={"email": email})

        # Get code
        import asyncio

        code = asyncio.run(mock_service.code_storage.get_code(email))

        # Try to verify - should fail (user doesn't exist)
        response = client.post("/auth/verify", json={"email": email, "code": code})

        assert response.status_code == 400


# GET /auth/me Tests (если есть endpoint для текущего пользователя)


def test_get_current_user_authenticated(client, mock_service):
    """Test getting current user with valid token"""
    with patch(
        "src.fastapi_email_auth.dependencies.get_auth_service",
        return_value=mock_service,
    ):
        email = "user@example.com"

        # Create user and get token
        import asyncio

        asyncio.run(mock_service.user_storage.get_or_create_user(email))
        token = mock_service._create_jwt_token(email)

        # Request with token
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email


def test_get_current_user_unauthenticated(client):
    """Test getting current user without token"""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token"""
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401


# Complete flow test


def test_complete_authentication_flow_via_api(client, mock_service):
    """Test complete flow through HTTP API"""
    with patch(
        "src.fastapi_email_auth.dependencies.get_auth_service",
        return_value=mock_service,
    ):
        email = "flowtest@example.com"

        # Pre-create user
        import asyncio

        asyncio.run(mock_service.user_storage.get_or_create_user(email))

        # Step 1: Request code
        response = client.post("/auth/send-code", json={"email": email})
        assert response.status_code == 200

        # Step 2: Get code from storage
        code = asyncio.run(mock_service.code_storage.get_code(email))

        # Step 3: Verify code
        response = client.post("/auth/verify", json={"email": email, "code": code})
        assert response.status_code == 200
        token = response.json()["access_token"]

        # Step 4: Use token to access protected endpoint
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["email"] == email
