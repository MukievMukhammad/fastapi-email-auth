"""Redis-based storage implementation"""

from typing import Optional

import redis.asyncio as redis

from ..interfaces import CodeStorage


class RedisCodeStorage(CodeStorage):
    """Redis implementation of code storage

    Stores verification codes with automatic expiration using Redis TTL.
    """

    def __init__(self, redis_url: str, key_prefix: str = "email_auth:"):
        """Initialize Redis storage

        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for all Redis keys
        """
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.prefix = key_prefix

    def _code_key(self, email: str) -> str:
        """Generate Redis key for code"""
        return f"{self.prefix}code:{email}"

    def _attempts_key(self, email: str) -> str:
        """Generate Redis key for attempts counter"""
        return f"{self.prefix}attempts:{email}"

    def _rate_limit_key(self, email: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"{self.prefix}ratelimit:{email}"

    async def save_code(self, email: str, code: str, ttl: int) -> None:
        """Save verification code with TTL"""
        await self.redis.setex(self._code_key(email), ttl, code)
        # Reset attempts counter
        await self.redis.delete(self._attempts_key(email))

    async def get_code(self, email: str) -> Optional[str]:
        """Retrieve verification code"""
        return await self.redis.get(self._code_key(email))

    async def delete_code(self, email: str) -> None:
        """Delete verification code and attempts"""
        await self.redis.delete(self._code_key(email), self._attempts_key(email))

    async def increment_attempts(self, email: str) -> int:
        """Increment and return attempts counter"""
        key = self._attempts_key(email)
        attempts = await self.redis.incr(key)

        # Set expiration to match code TTL
        code_ttl = await self.redis.ttl(self._code_key(email))
        if code_ttl > 0:
            await self.redis.expire(key, code_ttl)

        return attempts

    async def get_attempts(self, email: str) -> int:
        """Get current attempts counter"""
        attempts = await self.redis.get(self._attempts_key(email))
        return int(attempts) if attempts else 0

    async def reset_attempts(self, email: str) -> None:
        """Reset attempts counter"""
        await self.redis.delete(self._attempts_key(email))

    async def check_rate_limit(self, email: str) -> bool:
        """Check rate limiting"""
        key = self._rate_limit_key(email)
        exists = await self.redis.exists(key)

        if not exists:
            # Set rate limit for 60 seconds
            await self.redis.setex(key, 60, "1")
            return True

        return False

    async def close(self) -> None:
        """Close Redis connection"""
        await self.redis.close()
