import os
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from app.config import settings

def hash_pin(pin: str) -> str:
    """Hashes a numeric PIN using PBKDF2-HMAC-SHA256 with 100,000 iterations and random salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}:{key.hex()}"

def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verifies a plain PIN against its stored PBKDF2 hash using constant-time comparison."""
    try:
        if ":" not in hashed_pin:
            return False
        salt_hex, key_hex = hashed_pin.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        actual_key = hashlib.pbkdf2_hmac("sha256", plain_pin.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(actual_key, expected_key)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token for persistent sessions."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
