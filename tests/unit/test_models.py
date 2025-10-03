import pytest
from pydantic import ValidationError

from src.fastapi_email_auth.models import (
    AuthResponse,
    EmailLoginRequest,
    TokenResponse,
    VerifyCodeRequest,
)

# EmailLoginRequest Tests


def test_email_login_request_valid():
    """Test EmailLoginRequest with valid email"""
    request = EmailLoginRequest(email="test@example.com")
    assert request.email == "test@example.com"


def test_email_login_request_invalid_format():
    """Test EmailLoginRequest rejects invalid email format"""
    with pytest.raises(ValidationError) as exc_info:
        EmailLoginRequest(email="not-an-email")

    errors = exc_info.value.errors()
    assert any(error["type"] == "value_error" for error in errors)


def test_email_login_request_missing_email():
    """Test EmailLoginRequest requires email field"""
    with pytest.raises(ValidationError) as exc_info:
        EmailLoginRequest()

    errors = exc_info.value.errors()
    assert errors[0]["loc"] == ("email",)
    assert errors[0]["type"] == "missing"


def test_email_login_request_empty_string():
    """Test EmailLoginRequest rejects empty string"""
    with pytest.raises(ValidationError):
        EmailLoginRequest(email="")


def test_email_login_request_whitespace_trimmed():
    """Test EmailLoginRequest trims whitespace"""
    request = EmailLoginRequest(email="  test@example.com  ")
    assert request.email == "test@example.com"


def test_email_login_request_case_preserved():
    """Test EmailLoginRequest preserves email case"""
    request = EmailLoginRequest(email="Test@Example.COM")
    assert request.email == "Test@Example.COM"


# VerifyCodeRequest Tests


def test_verify_code_request_valid():
    """Test VerifyCodeRequest with valid data"""
    request = VerifyCodeRequest(email="test@example.com", code="abandon ability")
    assert request.email == "test@example.com"
    assert request.code == "abandon ability"


def test_verify_code_request_invalid_email():
    """Test VerifyCodeRequest rejects invalid email"""
    with pytest.raises(ValidationError):
        VerifyCodeRequest(email="invalid", code="abandon ability")


def test_verify_code_request_missing_code():
    """Test VerifyCodeRequest requires code field"""
    with pytest.raises(ValidationError) as exc_info:
        VerifyCodeRequest(email="test@example.com")

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("code",) for error in errors)


def test_verify_code_request_empty_code():
    """Test VerifyCodeRequest rejects empty code"""
    with pytest.raises(ValidationError):
        VerifyCodeRequest(email="test@example.com", code="")


def test_verify_code_request_code_whitespace():
    """Test VerifyCodeRequest handles code with spaces"""
    request = VerifyCodeRequest(email="test@example.com", code="  abandon ability  ")
    # Whitespace should be trimmed
    assert request.code.strip() == "abandon ability"


def test_verify_code_request_hyphen_separator():
    """Test VerifyCodeRequest accepts hyphen-separated codes"""
    request = VerifyCodeRequest(email="test@example.com", code="солнце-река")
    assert request.code == "солнце-река"


# AuthResponse Tests


def test_auth_response_success():
    """Test AuthResponse for successful code send"""
    response = AuthResponse(
        success=True,
        message="Code sent successfully",
        auth_request_id="abc123",
        expires_in=600,
    )
    assert response.success is True
    assert response.message == "Code sent successfully"
    assert response.auth_request_id == "abc123"
    assert response.expires_in == 600


def test_auth_response_failure():
    """Test AuthResponse for failure case"""
    response = AuthResponse(success=False, message="Rate limit exceeded")
    assert response.success is False
    assert response.message == "Rate limit exceeded"
    assert response.auth_request_id is None
    assert response.expires_in is None


def test_auth_response_optional_fields():
    """Test AuthResponse with only required fields"""
    response = AuthResponse(success=True, message="Done")
    assert response.success is True
    assert response.message == "Done"


def test_auth_response_json_serialization():
    """Test AuthResponse can be serialized to JSON"""
    response = AuthResponse(
        success=True, message="OK", auth_request_id="test123", expires_in=300
    )
    json_data = response.model_dump()

    assert json_data["success"] is True
    assert json_data["message"] == "OK"
    assert json_data["auth_request_id"] == "test123"
    assert json_data["expires_in"] == 300


# TokenResponse Tests


def test_token_response_valid():
    """Test TokenResponse with valid token"""
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    response = TokenResponse(access_token=token)

    assert response.access_token == token
    assert response.token_type == "bearer"


def test_token_response_default_token_type():
    """Test TokenResponse has default token_type"""
    response = TokenResponse(access_token="test_token")
    assert response.token_type == "bearer"


def test_token_response_custom_token_type():
    """Test TokenResponse accepts custom token_type"""
    response = TokenResponse(access_token="test_token", token_type="Bearer")
    assert response.token_type == "Bearer"


def test_token_response_empty_token():
    """Test TokenResponse rejects empty token"""
    with pytest.raises(ValidationError):
        TokenResponse(access_token="")


def test_token_response_json_structure():
    """Test TokenResponse JSON structure"""
    response = TokenResponse(access_token="abc123")
    json_data = response.model_dump()

    assert "access_token" in json_data
    assert "token_type" in json_data
    assert json_data["access_token"] == "abc123"
    assert json_data["token_type"] == "bearer"


# Model Integration Tests


def test_full_auth_flow_models():
    """Test models work together in authentication flow"""
    # Step 1: Login request
    login = EmailLoginRequest(email="user@example.com")
    assert login.email == "user@example.com"

    # Step 2: Auth response
    auth_resp = AuthResponse(
        success=True, message="Code sent", auth_request_id="req123", expires_in=600
    )
    assert auth_resp.success is True

    # Step 3: Verify request
    verify = VerifyCodeRequest(email="user@example.com", code="abandon ability")
    assert verify.code == "abandon ability"

    # Step 4: Token response
    token = TokenResponse(access_token="jwt_token_here")
    assert token.token_type == "bearer"


def test_model_validation_chain():
    """Test that validation works across model instances"""
    valid_email = "test@example.com"

    # Same email should be valid in both models
    login = EmailLoginRequest(email=valid_email)
    verify = VerifyCodeRequest(email=valid_email, code="test code")

    assert login.email == verify.email
