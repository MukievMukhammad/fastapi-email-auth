
# FastAPI Email Auth 📧🔐 (Beta)

Passwordless email authentication for FastAPI using BIP-39 mnemonic verification codes. Simple, secure, and production-ready.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118+-00a393.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🔐 **Passwordless authentication** - Users receive verification codes via email
- 🌍 **Multi-language support** - BIP-39 codes in 9 languages (English, Russian, Chinese, etc.)
- 🎯 **Easy to use** - Works out of the box with minimal configuration
- ⚡ **Async/await** - Fully asynchronous for high performance
- 🔄 **Pluggable storage** - In-memory, Redis, PostgreSQL, or custom implementations
- 🛡️ **Security first** - Rate limiting, attempt tracking, JWT tokens
- 📦 **Type-safe** - Full Pydantic validation
- 🧪 **Well tested** - 100% test coverage

## 📦 Installation

### Basic installation

```
pip install fastapi-email-auth
# or
uv add fastapi-email-auth
```

### With optional dependencies

```
# With Redis support
pip install fastapi-email-auth[redis]

# With PostgreSQL support
pip install fastapi-email-auth[postgres]

# With all optional dependencies
pip install fastapi-email-auth[all]
```

## 🚀 Quick Start

### 1. Create `.env` file

```
EMAIL_AUTH_SMTP_HOST=smtp.gmail.com
EMAIL_AUTH_SMTP_PORT=587
EMAIL_AUTH_SMTP_USER=your-email@gmail.com
EMAIL_AUTH_SMTP_PASSWORD=your-app-password
EMAIL_AUTH_JWT_SECRET=your-secret-key-at-least-32-characters
```

### 2. Add to your FastAPI app

```
from fastapi import FastAPI
from fastapi_email_auth import router

app = FastAPI()

# Add authentication routes
app.include_router(router, prefix="/auth")
```

### 3. That's it! 🎉

Your API now has these endpoints:

- `POST /auth/send-code` - Send verification code to email
- `POST /auth/verify` - Verify code and get JWT token
- `GET /auth/me` - Get current user (protected)

## 📖 Usage Examples

### Basic Authentication Flow

```
# 1. User requests verification code
POST /auth/send-code
{
  "email": "user@example.com"
}

# Response:
{
  "success": true,
  "message": "Code sent to email",
  "expires_in": 600
}

# 2. User receives email with code like "abandon ability"

# 3. User submits code
POST /auth/verify
{
  "email": "user@example.com",
  "code": "abandon ability"
}

# Response:
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}

# 4. Access protected endpoints
GET /auth/me
Authorization: Bearer eyJhbGci...

# Response:
{
  "email": "user@example.com",
  "created_at": "2025-10-04T10:00:00Z",
  "last_login": "2025-10-04T10:05:00Z"
}
```

### Using Protected Routes

```
from fastapi import FastAPI, Depends
from fastapi_email_auth import router, get_current_user

app = FastAPI()
app.include_router(router, prefix="/auth")

@app.get("/profile")
async def get_profile(email: str = Depends(get_current_user)):
    """This route requires authentication"""
    return {"email": email, "subscription": "premium"}

@app.get("/admin")
async def admin_panel(email: str = Depends(get_current_user)):
    """Check if user is admin"""
    if email not in ["admin@example.com"]:
        raise HTTPException(403, "Admin access required")
    return {"message": "Welcome, admin!"}
```

## ⚙️ Configuration

All settings are configured via environment variables with `EMAIL_AUTH_` prefix:

### SMTP Settings

```
EMAIL_AUTH_SMTP_HOST=smtp.gmail.com
EMAIL_AUTH_SMTP_PORT=587
EMAIL_AUTH_SMTP_USER=noreply@example.com
EMAIL_AUTH_SMTP_PASSWORD=app-password
EMAIL_AUTH_SMTP_USE_TLS=true
EMAIL_AUTH_SMTP_FROM_EMAIL=noreply@example.com  # Optional, defaults to SMTP_USER
```

### JWT Settings

```
EMAIL_AUTH_JWT_SECRET=your-secret-key-min-32-chars
EMAIL_AUTH_JWT_ALGORITHM=HS256
EMAIL_AUTH_JWT_EXPIRY_DAYS=7
```

### Code Generation

```
EMAIL_AUTH_CODE_WORD_COUNT=2              # Number of words (1-12)
EMAIL_AUTH_CODE_LANGUAGE=russian          # english, russian, spanish, etc.
EMAIL_AUTH_CODE_SEPARATOR=-               # Separator between words
EMAIL_AUTH_CODE_TTL=600                   # Code validity in seconds
```

### Security

```
EMAIL_AUTH_MAX_ATTEMPTS=3                 # Max verification attempts
EMAIL_AUTH_RATE_LIMIT_WINDOW=60          # Rate limit window in seconds
```

### Storage (Optional)

```
# Redis for production
EMAIL_AUTH_REDIS_URL=redis://localhost:6379/0
EMAIL_AUTH_REDIS_KEY_PREFIX=myapp:auth:

# PostgreSQL for user storage
EMAIL_AUTH_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
```

## 🔧 Advanced Integration

### Custom Storage Implementation

Implement your own storage backends:

```
from fastapi import FastAPI
from fastapi_email_auth import (
    EmailAuthService,
    set_custom_service,
    router
)
from fastapi_email_auth.storage.redis import RedisCodeStorage
from my_app.storage import MyUserStorage  # Your implementation

app = FastAPI()

# Create custom service on startup
@app.on_event("startup")
async def setup_auth():
    code_storage = RedisCodeStorage("redis://localhost:6379/0")
    user_storage = MyUserStorage()  # Your PostgreSQL/MongoDB/etc implementation
    
    service = EmailAuthService(
        code_storage=code_storage,
        user_storage=user_storage,
        smtp_host="smtp.yandex.ru",
        smtp_port=587,
        smtp_user="noreply@myapp.com",
        smtp_password="password",
        jwt_secret="secret",
        code_language="russian",
        max_attempts=5
    )
    
    set_custom_service(service)

app.include_router(router, prefix="/auth")
```

### Implementing Custom UserStorage

```
from fastapi_email_auth.interfaces import UserStorage
from typing import Optional
from datetime import datetime, timezone

class PostgreSQLUserStorage(UserStorage):
    def __init__(self, connection_string: str):
        self.db = create_async_engine(connection_string)
    
    async def get_user(self, email: str) -> Optional[dict]:
        async with self.db.begin() as conn:
            result = await conn.execute(
                "SELECT * FROM users WHERE email = $1", email
            )
            return dict(result.fetchone()) if result else None
    
    async def get_or_create_user(self, email: str) -> dict:
        user = await self.get_user(email)
        if not user:
            async with self.db.begin() as conn:
                await conn.execute(
                    "INSERT INTO users (email, created_at) VALUES ($1, $2)",
                    email, datetime.now(timezone.utc)
                )
            user = await self.get_user(email)
        return user
    
    async def update_last_login(self, email: str) -> None:
        async with self.db.begin() as conn:
            await conn.execute(
                "UPDATE users SET last_login = $1 WHERE email = $2",
                datetime.now(timezone.utc), email
            )
```

### Custom Email Templates

Override email sending with custom templates:

```
from fastapi_email_auth import EmailAuthService
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import aiosmtplib

class CustomEmailService(EmailAuthService):
    async def _send_email(self, email: str, code: str) -> None:
        message = MIMEMultipart("alternative")
        message["Subject"] = "🔐 Your Login Code"
        message["From"] = self.smtp_config["username"]
        message["To"] = email
        
        html = f"""
        <html>
          <body style="font-family: Arial;">
            <div style="max-width: 600px; margin: 0 auto;">
              <h1>Your verification code:</h1>
              <div style="background: #4CAF50; padding: 20px; text-align: center;">
                <h2 style="color: white; font-size: 36px;">{code}</h2>
              </div>
              <p>Valid for {self.code_ttl // 60} minutes.</p>
            </div>
          </body>
        </html>
        """
        
        message.attach(MIMEText(html, "html"))
        await aiosmtplib.send(message, **self.smtp_config)
```

### Integration with Existing User System

```
from fastapi import FastAPI, Depends
from fastapi_email_auth import router, EmailAuthService, get_auth_service

app = FastAPI()
app.include_router(router, prefix="/auth")

@app.post("/auth/register")
async def register(
    email: str,
    name: str,
    service: EmailAuthService = Depends(get_auth_service)
):
    """Custom registration with additional fields"""
    
    # 1. Validate email doesn't exist
    existing = await service.user_storage.get_user(email)
    if existing:
        raise HTTPException(400, "Email already registered")
    
    # 2. Send verification code
    result = await service.send_verification_code(email)
    
    # 3. Store additional user data
    await your_db.store_pending_user(email, name)
    
    return {"message": "Verification code sent", "expires_in": result["expires_in"]}

@app.post("/auth/complete-registration")
async def complete_registration(
    email: str,
    code: str,
    service: EmailAuthService = Depends(get_auth_service)
):
    """Verify code and complete registration"""
    
    # Verify code and create user
    token = await service.verify_code(email, code, auto_create_user=True)
    
    # Retrieve and save additional data
    pending_user = await your_db.get_pending_user(email)
    await your_db.create_user(email, pending_user.name)
    
    return {"access_token": token, "token_type": "bearer"}
```

## 🌍 Multi-Language Support

Supported BIP-39 languages:

```
# English (default)
EMAIL_AUTH_CODE_LANGUAGE=english
# "abandon ability"

# Russian
EMAIL_AUTH_CODE_LANGUAGE=russian
# "солнце-река"

# Spanish
EMAIL_AUTH_CODE_LANGUAGE=spanish
# "casa-perro"

# Also supported: chinese_simplified, chinese_traditional, 
# french, italian, japanese, korean
```

## 🛡️ Security Features

### Rate Limiting

Prevents spam by limiting code requests:

```
EMAIL_AUTH_RATE_LIMIT_WINDOW=60  # 1 minute between requests
```

### Attempt Tracking

Limits verification attempts per code:

```
EMAIL_AUTH_MAX_ATTEMPTS=3  # Lock after 3 failed attempts
```

### JWT Expiration

Tokens automatically expire:

```
EMAIL_AUTH_JWT_EXPIRY_DAYS=7  # Token valid for 7 days
```

## 🧪 Testing

```
# Install dev dependencies
pip install fastapi-email-auth[dev]

# Run tests
pytest

# With coverage
pytest --cov=fastapi_email_auth --cov-report=html
```

## 🚀 Production Deployment

### With Docker

```
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### With Docker Compose

```
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### Environment Variables for Production

```
# Use strong secrets
EMAIL_AUTH_JWT_SECRET=${RANDOM_SECRET_FROM_SECRETS_MANAGER}

# Production SMTP
EMAIL_AUTH_SMTP_HOST=smtp.yandex.ru
EMAIL_AUTH_SMTP_USER=${SMTP_USER_FROM_SECRETS}
EMAIL_AUTH_SMTP_PASSWORD=${SMTP_PASSWORD_FROM_SECRETS}

# Redis for scalability
EMAIL_AUTH_REDIS_URL=redis://redis:6379/0

# Database
EMAIL_AUTH_DATABASE_URL=${DATABASE_URL_FROM_SECRETS}
```

## 📚 API Reference

### Endpoints

#### `POST /auth/send-code`

Send verification code to email.

**Request:**
```
{
  "email": "user@example.com"
}
```

**Response:**
```
{
  "success": true,
  "message": "Code sent to email",
  "expires_in": 600
}
```

#### `POST /auth/verify`

Verify code and receive JWT token. Requires user to exist.

**Request:**
```
{
  "email": "user@example.com",
  "code": "abandon ability"
}
```

**Response:**
```
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

#### `POST /auth/register-and-verify`

Verify code and auto-create user if doesn't exist.

**Request:**
```
{
  "email": "newuser@example.com",
  "code": "abandon ability"
}
```

**Response:**
```
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

#### `GET /auth/me`

Get current authenticated user.

**Headers:**
```
Authorization: Bearer eyJhbGci...
```

**Response:**
```
{
  "email": "user@example.com",
  "created_at": "2025-10-04T10:00:00Z",
  "last_login": "2025-10-04T10:05:00Z"
}
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [GitHub Repository](https://github.com/MukievMukhammad/fastapi-email-auth)
- [PyPI Package](https://pypi.org/project/fastapi-email-auth/)
- [Documentation](https://github.com/MukievMukhammad/fastapi-email-auth#readme)
- [Issue Tracker](https://github.com/MukievMukhammad/fastapi-email-auth/issues)

## 💬 Support

- 📧 Email: bronze_58_radar@icloud.com
- 🐛 Issues: [GitHub Issues](https://github.com/MukievMukhammad/fastapi-email-auth/issues)

---

Made with ❤️ by [Mukiev Mukhammad](https://github.com/MukievMukhammad)
