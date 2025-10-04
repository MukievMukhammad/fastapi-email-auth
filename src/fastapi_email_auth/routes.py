"""FastAPI routes for email authentication"""

from fastapi import APIRouter, Depends, HTTPException, status

from .dependencies import get_auth_service, get_current_user
from .models import AuthResponse, EmailLoginRequest, TokenResponse, VerifyCodeRequest
from .service import EmailAuthService

router = APIRouter(tags=["authentication"])


@router.post(
    "/send-code",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Send verification code",
    description="Sends a verification code to the provided email address",
)
async def send_verification_code(
    request: EmailLoginRequest, service: EmailAuthService = Depends(get_auth_service)
) -> AuthResponse:
    """Send verification code to user's email

    Args:
        request: Email login request with user's email
        service: Authentication service instance

    Returns:
        AuthResponse with success status and expiration time

    Raises:
        HTTPException: 429 if rate limit exceeded
        HTTPException: 500 if email sending fails
    """
    try:
        result = await service.send_verification_code(request.email)

        return AuthResponse(
            success=True, message="Code sent to email", expires_in=result["expires_in"]
        )

    except ValueError as e:
        error_msg = str(e).lower()

        # Rate limit error
        if "rate limit" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e)
            )

        # Other validation errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification code: {str(e)}",
        )


@router.post(
    "/verify",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify code and get token",
    description="Verifies the code and returns a JWT access token",
)
async def verify_code(
    request: VerifyCodeRequest, service: EmailAuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Verify code and generate JWT token

    Args:
        request: Verification request with email and code
        service: Authentication service instance

    Returns:
        TokenResponse with JWT access token

    Raises:
        HTTPException: 400 if code is invalid or user doesn't exist
        HTTPException: 500 if token generation fails
    """
    try:
        # Try to verify code (default: auto_create_user=False)
        token = await service.verify_code(
            request.email,
            request.code,
            auto_create_user=False,  # Explicitly set to False
        )

        return TokenResponse(access_token=token)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}",
        )


@router.post(
    "/register-and-verify",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Register new user and verify code",
    description="Verifies code and creates user account if doesn't exist",
)
async def register_and_verify(
    request: VerifyCodeRequest, service: EmailAuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Verify code and auto-create user if needed

    This endpoint is for user registration flow where new users
    are automatically created during verification.

    Args:
        request: Verification request with email and code
        service: Authentication service instance

    Returns:
        TokenResponse with JWT access token

    Raises:
        HTTPException: 400 if code is invalid
        HTTPException: 500 if token generation fails
    """
    try:
        # Auto-create user if doesn't exist
        token = await service.verify_code(
            request.email,
            request.code,
            auto_create_user=True,  # Allow user creation
        )

        return TokenResponse(access_token=token)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Returns information about the authenticated user",
)
async def get_current_user_info(
    email: str = Depends(get_current_user),
    service: EmailAuthService = Depends(get_auth_service),
) -> dict:
    """Get current authenticated user information

    Args:
        email: Current user's email from JWT token
        service: Authentication service instance

    Returns:
        User information dictionary

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 404 if user not found
    """
    try:
        user = await service.user_storage.get_user(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return {
            "email": user["email"],
            "created_at": user["created_at"].isoformat()
            if user.get("created_at")
            else None,
            "last_login": user["last_login"].isoformat()
            if user.get("last_login")
            else None,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}",
        )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Invalidates the current session (client-side token removal)",
)
async def logout() -> dict:
    """Logout current user

    Note: Since we use stateless JWT tokens, actual logout happens
    on the client side by removing the token. This endpoint is mainly
    for API consistency and future server-side logout implementation.

    Returns:
        Success message
    """
    return {"success": True, "message": "Logged out successfully"}
