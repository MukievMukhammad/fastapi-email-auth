from abc import ABC, abstractmethod
from typing import Optional


class CodeStorage(ABC):
    """Interface for verification code storage

    Defines the contract that any code storage implementation must follow.
    This allows users to plug in their own storage backend (Redis, PostgreSQL,
    files, etc.) while maintaining a consistent API.
    """

    @abstractmethod
    async def save_code(self, email: str, code: str, ttl: int) -> None:
        """Save verification code with time-to-live in seconds

        Args:
            email: User's email address
            code: Generated verification code (BIP-39 words)
            ttl: Time-to-live in seconds before code expires
        """
        pass

    @abstractmethod
    async def get_code(self, email: str) -> Optional[str]:
        """Retrieve stored verification code

        Args:
            email: User's email address

        Returns:
            Verification code if exists and not expired, None otherwise
        """
        pass

    @abstractmethod
    async def delete_code(self, email: str) -> None:
        """Delete verification code after successful use

        Args:
            email: User's email address
        """
        pass

    @abstractmethod
    async def increment_attempts(self, email: str) -> int:
        """Increment failed verification attempts counter

        Args:
            email: User's email address

        Returns:
            Current number of failed attempts
        """
        pass

    @abstractmethod
    async def get_attempts(self, email: str) -> int:
        """Return attempts count

        Args:
            email: User's email address

        Returns:
            Current number of failed attempts
        """
        pass

    @abstractmethod
    async def check_rate_limit(self, email: str) -> bool:
        """Check if user exceeded rate limit for code requests

        Args:
            email: User's email address

        Returns:
            True if user can request a new code, False if rate limited
        """
        pass


class UserStorage(ABC):
    """Interface for user data persistence"""

    @abstractmethod
    async def get_user(self, email: str) -> dict | None:
        """Get user by email without creating

        Args:
            email: User's email address

        Returns:
            User data dictionary if exists, None otherwise
        """
        pass

    @abstractmethod
    async def get_or_create_user(self, email: str) -> dict:
        """Get existing user or create new one

        Args:
            email: User's email address

        Returns:
            User data dictionary with at least 'email' field
        """
        pass

    @abstractmethod
    async def update_last_login(self, email: str) -> None:
        """Update timestamp of user's last successful login

        Args:
            email: User's email address
        """
        pass
