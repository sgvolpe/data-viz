# auth.py
import hashlib
from datetime import datetime, timedelta

import jwt
from passlib.context import CryptContext

from core.config import settings

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -----------------------------
# Password hashing / verification
# -----------------------------
def hash_password(password: str) -> str:
    """
    Pre-hash password with SHA-256 to handle passwords longer than 72 bytes,
    then hash with bcrypt.
    """
    sha = hashlib.sha256(password.encode()).digest()
    return pwd.hash(sha)


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password by first SHA-256 hashing, then comparing with bcrypt hash.
    """
    sha = hashlib.sha256(password.encode()).digest()
    return pwd.verify(sha, hashed)


# -----------------------------
# JWT token creation
# -----------------------------
def create_access_token(user_id: str, expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
