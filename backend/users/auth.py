"""
Authentication utilities for password hashing, verification, and JWT token creation.

This module provides:
- Secure password hashing using SHA-256 + bcrypt
- Password verification
- Generation of signed JSON Web Tokens (JWT) for user authentication

───────────────────────────────────────────────────────────────────────────────
PASSWORD HASHING
───────────────────────────────────────────────────────────────────────────────
bcrypt only accepts passwords up to 72 bytes. To support arbitrarily long
passwords, we first pre-hash the password with SHA-256, then hash the digest
with bcrypt. The stored value in the database is the bcrypt hash.

Workflow:
    stored_hash = hash_password("mysecret")
    verify_password("mysecret", stored_hash)  → True

───────────────────────────────────────────────────────────────────────────────
WHAT IS A JWT?
───────────────────────────────────────────────────────────────────────────────
A **JSON Web Token (JWT)** is a compact, URL-safe token used for stateless
authentication. It consists of three parts:

1. **Header** – contains algorithm and token type
2. **Payload** – contains claims, e.g. user_id, expiration time
3. **Signature** – ensures the token hasn't been tampered with

Example JWT structure:
    header.payload.signature

JWTs are **signed**, not encrypted—anyone can read the payload, but only the
server can generate or validate the signature.

───────────────────────────────────────────────────────────────────────────────
HOW JWT IS USED IN THIS PROJECT
───────────────────────────────────────────────────────────────────────────────
`create_access_token()` generates a signed JWT containing:
- `sub`: the user ID
- `exp`: expiration time

Usage (FastAPI example):
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}

Client usage:
    - The client stores the token (usually localStorage or cookies)
    - Sends it on each request:

        Authorization: Bearer <token>

Server-side verification happens inside your dependency:
    jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])

If the signature or expiration is invalid → 401 Unauthorized.

───────────────────────────────────────────────────────────────────────────────
"""
import hashlib
from datetime import datetime, timedelta

import jwt
from passlib.context import CryptContext

from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)


def create_access_token(user_id: str, expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
