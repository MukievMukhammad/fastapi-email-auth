"""Factory for creating storage instances based on configuration"""

from ..config import EmailAuthSettings
from ..interfaces import CodeStorage, UserStorage


def create_code_storage(settings: EmailAuthSettings) -> CodeStorage:
    """Create code storage based on configuration

    Args:
        settings: Application settings

    Returns:
        CodeStorage implementation (Redis or in-memory)
    """
    if settings.redis_url:
        # Use Redis if configured
        from .redis import RedisCodeStorage

        return RedisCodeStorage(
            redis_url=settings.redis_url, key_prefix=settings.redis_key_prefix
        )
    else:
        # Fallback to in-memory
        from .memory import InMemoryCodeStorage

        return InMemoryCodeStorage()


def create_user_storage(settings: EmailAuthSettings) -> UserStorage:
    """Create user storage based on configuration

    Args:
        settings: Application settings

    Returns:
        UserStorage implementation (Database or in-memory)
    """
    if settings.database_url:
        # Use database if configured
        pass
        # from .database import DatabaseUserStorage  # TODO: add Postgres by default

        # return DatabaseUserStorage(settings.database_url)
    else:
        # Fallback to in-memory
        from .memory import InMemoryUserStorage

        return InMemoryUserStorage()
