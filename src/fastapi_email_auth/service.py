"""Authentication service for email-based passwordless login"""

from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import aiosmtplib
from jose import jwt

from .interfaces import CodeStorage, UserStorage
from .utils.bip39 import BIP39Generator, Language


class EmailAuthService:
    """Email-based authentication service

    Handles verification code generation, email sending, and JWT token creation.
    """

    def __init__(
        self,
        code_storage: CodeStorage,
        user_storage: UserStorage,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        word_count: int = 2,
        code_language: Language = "english",
        code_separator: str = " ",
        code_ttl: int = 600,
        max_attempts: int = 3,
        jwt_expiry_days: int = 7,
    ):
        """Initialize authentication service

        Args:
            code_storage: Storage implementation for verification codes
            user_storage: Storage implementation for user data
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            jwt_secret: Secret key for JWT signing
            jwt_algorithm: JWT algorithm (default: HS256)
            word_count: Number of BIP-39 words in code (default: 2)
            code_language: Language for BIP-39 words (default: english)
            code_separator: Separator between words (default: space)
            code_ttl: Code time-to-live in seconds (default: 600)
            max_attempts: Maximum verification attempts (default: 3)
            jwt_expiry_days: JWT token validity in days (default: 7)

        Raises:
            ValueError: If max_attempts is less than 1
        """
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        self.code_storage = code_storage
        self.user_storage = user_storage

        self.smtp_config = {
            "hostname": smtp_host,
            "port": smtp_port,
            "username": smtp_user,
            "password": smtp_password,
            "use_tls": True,
        }

        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.jwt_expiry_days = jwt_expiry_days

        self.bip39_generator = BIP39Generator(code_language)
        self.word_count = word_count
        self.code_separator = code_separator
        self.code_ttl = code_ttl
        self.max_attempts = max_attempts

    async def send_verification_code(
        self, email: str, word_count: Optional[int] = None
    ) -> dict:
        """Send verification code to user email

        Args:
            email: User's email address
            word_count: Optional custom word count (overrides default)

        Returns:
            Dictionary with expires_in field

        Raises:
            ValueError: If rate limit is exceeded
        """
        # Check rate limit
        if not await self.code_storage.check_rate_limit(email):
            raise ValueError("Rate limit exceeded. Please try again later.")

        # Generate BIP-39 code
        words = word_count if word_count is not None else self.word_count
        code = self.bip39_generator.generate_code(words, self.code_separator)

        # Save code to storage
        await self.code_storage.save_code(email, code, self.code_ttl)

        # Send email
        await self._send_email(email, code)

        return {"expires_in": self.code_ttl}

    async def verify_code(
        self, email: str, code: str, auto_create_user: bool = False
    ) -> str:
        """Verify code and generate JWT token

        Args:
            email: User's email address
            code: Verification code to check
            auto_create_user: If True, creates new user automatically.
                            If False (default), raises error for non-existent users.

        Returns:
            JWT access token

        Raises:
            ValueError: If code is invalid, expired, max attempts exceeded,
                    or user doesn't exist (when auto_create_user=False)
        """
        # Validate code format
        if not self.bip39_generator.validate_code(code, self.code_separator):
            await self.code_storage.increment_attempts(email)
            raise ValueError("Invalid code format")

        # Get stored code
        stored_code = await self.code_storage.get_code(email)
        if not stored_code:
            raise ValueError("Code expired or not found")

        # Check if max attempts already exceeded
        current_attempts = await self.code_storage.get_attempts(email)
        if current_attempts >= self.max_attempts:
            await self.code_storage.delete_code(email)
            raise ValueError("Maximum verification attempts exceeded")

        # Verify code matches
        if stored_code.lower() != code.lower():
            await self.code_storage.increment_attempts(email)
            raise ValueError("Invalid code")

        # Success - cleanup
        await self.code_storage.delete_code(email)

        # Handle user creation/retrieval based on flag
        if auto_create_user:
            # Create user if doesn't exist
            user = await self.user_storage.get_or_create_user(email)
            await self.user_storage.update_last_login(email)
        else:
            # Check if user exists, error if not
            user = await self._get_existing_user(email)
            if not user:
                raise ValueError(f"User with email {email} does not exist")
            await self.user_storage.update_last_login(email)

        # Generate JWT token
        token = self._create_jwt_token(email)
        return token

    async def _get_existing_user(self, email: str) -> dict | None:
        """Check if user exists without creating

        Args:
            email: User's email address

        Returns:
            User data if exists, None otherwise
        """
        # Проверяем существование через user_storage
        # Нужно добавить метод в интерфейс UserStorage
        try:
            # Если у storage есть метод get_user (без create)
            if hasattr(self.user_storage, "get_user"):
                return await self.user_storage.get_user(email)
            else:
                # Fallback: используем get_or_create_user но проверяем,
                # был ли пользователь создан только что
                # (требует изменения интерфейса)
                raise NotImplementedError(
                    "UserStorage must implement get_user() method "
                    "for non-auto-create mode"
                )
        except Exception:
            return None

    def _create_jwt_token(self, email: str) -> str:
        """Create JWT access token

        Args:
            email: User's email address

        Returns:
            Encoded JWT token
        """
        expires_delta = timedelta(days=self.jwt_expiry_days)
        expire = datetime.now(timezone.utc) + expires_delta

        payload = {"sub": email, "exp": expire, "iat": datetime.now(timezone.utc)}

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def decode_token(self, token: str) -> str:
        """Decode and verify JWT token

        Args:
            token: JWT token to decode

        Returns:
            Email address from token

        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )
            email = payload.get("sub")
            if not email:
                raise ValueError("Invalid token payload")
            return email
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    async def _send_email(self, email: str, code: str) -> None:
        """Send verification code via email

        Args:
            email: Recipient email address
            code: Verification code to send
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = "Verification Code"
        message["From"] = self.smtp_config["username"]
        message["To"] = email

        # Plain text version
        text = f"""
Your verification code:

{code}

This code is valid for {self.code_ttl // 60} minutes.

If you did not request this code, please ignore this email.
        """

        # HTML version
        html = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #4CAF50;">Verification Code</h2>
      <p>Your verification code is:</p>
      <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
        <h1 style="color: #4CAF50; font-size: 32px; letter-spacing: 3px; margin: 0;">
          {code}
        </h1>
      </div>
      <p>This code is valid for <strong>{self.code_ttl // 60} minutes</strong>.</p>
      <p style="color: #666; font-size: 12px; margin-top: 30px;">
        If you did not request this code, please ignore this email.
      </p>
    </div>
  </body>
</html>
        """

        # Attach both versions
        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))

        # Send email
        await aiosmtplib.send(message, **self.smtp_config)
