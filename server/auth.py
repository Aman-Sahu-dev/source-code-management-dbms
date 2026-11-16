"""Simple token-based auth using SHA-256."""

import hashlib
import os
import time

# In-memory token store: token -> username
_token_store: dict[str, str] = {}


def hash_password(plain: str) -> str:
    secret = os.getenv("SECRET_KEY", "changeme")
    return hashlib.sha256(f"{plain}{secret}".encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


def create_token(username: str) -> str:
    secret = os.getenv("SECRET_KEY", "changeme")
    raw = f"{username}{secret}{time.time()}"
    token = hashlib.sha256(raw.encode()).hexdigest()
    _token_store[token] = username
    return token


def validate_token(token: str) -> str | None:
    """Return username if valid, else None."""
    return _token_store.get(token)


def revoke_token(token: str) -> None:
    _token_store.pop(token, None)
