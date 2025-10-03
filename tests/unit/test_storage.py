import pytest

from src.fastapi_email_auth.storage.memory import InMemoryCodeStorage


@pytest.mark.asyncio
async def test_save_and_get_code():
    """Test saving and retrieving verification code"""
    storage = InMemoryCodeStorage()
    email = "test@example.com"
    code = "abandon ability"

    await storage.save_code(email, code, ttl=600)
    retrieved = await storage.get_code(email)

    assert retrieved == code


@pytest.mark.asyncio
async def test_code_expiration():
    """Test that codes expire after TTL period"""
    storage = InMemoryCodeStorage()
    email = "test@example.com"

    # Save code with 0 second TTL (expires immediately)
    await storage.save_code(email, "test code", ttl=0)

    # Simulate delay to ensure expiration
    import asyncio

    await asyncio.sleep(0.1)

    # Code should be expired and return None
    retrieved = await storage.get_code(email)
    assert retrieved is None


@pytest.mark.asyncio
async def test_increment_attempts():
    """Test failed attempts counter increments correctly"""
    storage = InMemoryCodeStorage()
    email = "test@example.com"

    await storage.save_code(email, "test", ttl=600)

    # Each increment should return updated counter
    assert await storage.increment_attempts(email) == 1
    assert await storage.increment_attempts(email) == 2
    assert await storage.increment_attempts(email) == 3


@pytest.mark.asyncio
async def test_delete_code():
    """Test code deletion after successful verification"""
    storage = InMemoryCodeStorage()
    email = "test@example.com"

    # Save code
    await storage.save_code(email, "test", ttl=600)

    # Delete code
    await storage.delete_code(email)

    # Code should no longer exist
    assert await storage.get_code(email) is None


@pytest.mark.asyncio
async def test_attempts_reset_on_new_code():
    """Test that attempts counter resets when new code is saved"""
    storage = InMemoryCodeStorage()
    email = "test@example.com"

    # Save code and increment attempts
    await storage.save_code(email, "first code", ttl=600)
    await storage.increment_attempts(email)
    await storage.increment_attempts(email)
    assert await storage.get_attempts(email) == 2

    # Save new code - attempts should reset
    await storage.save_code(email, "second code", ttl=600)
    assert await storage.get_attempts(email) == 0


@pytest.mark.asyncio
async def test_get_nonexistent_code():
    """Test getting code for email that has no code"""
    storage = InMemoryCodeStorage()

    # Try to get code for email that never received one
    retrieved = await storage.get_code("nonexistent@example.com")
    assert retrieved is None


@pytest.mark.asyncio
async def test_rate_limit():
    """Test rate limiting functionality"""
    storage = InMemoryCodeStorage()
    email = "test@example.com"

    # First request should be allowed
    assert await storage.check_rate_limit(email)

    # Immediate second request should be rate limited
    assert await storage.check_rate_limit(email)
