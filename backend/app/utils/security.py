# security.py - JWT encode/decode and password hashing
# Used for login tokens and (optional) password storage

from datetime import datetime, timedelta
from typing import Optional, Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Password hashing - used if we add password-based login later
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(sub: str, email: Optional[str] = None, role: str = "student") -> str:
    """Create a JWT access token. sub = user id (or email/enrollment for lookup)."""
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": sub,
        "email": email,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify JWT. Returns payload dict or None if invalid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_password(password: str) -> str:
    """Hash a password (for future use)."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash (for future use)."""
    return pwd_context.verify(plain, hashed)
