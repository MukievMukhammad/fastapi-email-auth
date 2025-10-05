from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from ..interfaces import CodeStorage, UserStorage


class InMemoryCodeStorage(CodeStorage):
    """In-memory storage implementation for testing and development

    This implementation stores verification codes in memory with automatic
    expiration. Suitable for testing, development, and small-scale deployments.
    Not recommended for production use with multiple server instances.
    """

    def __init__(self, rate_limit_window: int = 60):
        # Store codes with expiration time: {email: (code, expiry_datetime)}
        self.codes: Dict[str, tuple[str, datetime]] = {}

        # Track failed verification attempts per email
        self.attempts: Dict[str, int] = {}

        # Rate limiting timestamps: {email: next_allowed_request_time}
        self.rate_limits: Dict[str, datetime] = {}
        self.rate_limit_window = rate_limit_window

    async def save_code(self, email: str, code: str, ttl: int) -> None:
        """Save verification code with automatic expiration

        Args:
            email: User's email address
            code: Generated BIP-39 verification code
            ttl: Time-to-live in seconds
        """
        expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        self.codes[email] = (code, expiry)
        self.attempts[email] = 0  # Reset attempts counter on new code

    async def get_code(self, email: str) -> Optional[str]:
        """Retrieve stored verification code if not expired

        Args:
            email: User's email address

        Returns:
            Verification code if exists and valid, None if expired or not found
        """
        if email not in self.codes:
            return None

        code, expiry = self.codes[email]

        # Check if code has expired
        if datetime.now(timezone.utc) > expiry:
            # Automatically clean up expired code
            await self.delete_code(email)
            return None

        return code

    async def delete_code(self, email: str) -> None:
        """Delete verification code and reset attempts counter

        Called after successful verification or when code expires.

        Args:
            email: User's email address
        """
        self.codes.pop(email, None)
        self.attempts.pop(email, None)

    async def increment_attempts(self, email: str) -> int:
        """Increment failed verification attempts counter

        Args:
            email: User's email address

        Returns:
            Current number of failed attempts after increment
        """
        self.attempts[email] = self.attempts.get(email, 0) + 1
        return self.attempts[email]

    async def get_attempts(self, email: str) -> int:
        """Get current number of failed verification attempts

        Args:
            email: User's email address

        Returns:
            Number of failed attempts (0 if no attempts recorded)
        """
        return self.attempts.get(email, 0)

    async def reset_attempts(self, email: str) -> None:
        """Reset failed attempts counter to zero

        Args:
            email: User's email address
        """
        self.attempts[email] = 0

    async def check_rate_limit(self, email: str) -> bool:
        """Check if user can request a new verification code

        Implements basic rate limiting to prevent abuse.

        Args:
            email: User's email address

        Returns:
            True if user can request code, False if rate limited
        """
        if email not in self.rate_limits:
            # First request - allow and set rate limit
            self.rate_limits[email] = datetime.now(timezone.utc) + timedelta(
                minutes=self.rate_limit_window
            )
            return True

        # Check if rate limit period has passed
        return datetime.now(timezone.utc) > self.rate_limits[email]


class InMemoryUserStorage(UserStorage):
    """In-memory user storage implementation for testing"""

    def __init__(self):
        # Store user data: {email: user_dict}
        self.users: Dict[str, dict] = {}

    async def get_user(self, email: str) -> dict | None:
        """Get user by email without creating

        Args:
            email: User's email address

        Returns:
            User data if exists, None otherwise
        """
        return self.users.get(email)

    async def get_or_create_user(self, email: str) -> dict:
        """Get existing user or create new one

        Args:
            email: User's email address

        Returns:
            User data dictionary containing email, created_at, and last_login
        """
        if email not in self.users:
            self.users[email] = {
                "email": email,
                "created_at": datetime.now(timezone.utc),
                "last_login": None,
            }
        return self.users[email]

    async def update_last_login(self, email: str) -> None:
        """Update user's last login timestamp

        Called after successful authentication.

        Args:
            email: User's email address
        """
        if email in self.users:
            self.users[email]["last_login"] = datetime.now(timezone.utc)
