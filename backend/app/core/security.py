import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def _encode(sub: str, token_type: str, expires: timedelta, extra: dict | None = None) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload = {"sub": sub, "type": token_type, "iat": now, "exp": now + expires, **(extra or {})}
    return jwt.encode(payload, s.JWT_SECRET, algorithm=s.JWT_ALGORITHM)


def create_access_token(user_id: str) -> str:
    return _encode(user_id, "access", timedelta(minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(user_id: str) -> str:
    return _encode(user_id, "refresh", timedelta(days=get_settings().REFRESH_TOKEN_EXPIRE_DAYS))


def password_fingerprint(hashed_password: str) -> str:
    return hashlib.sha256(hashed_password.encode()).hexdigest()[:16]


def create_reset_token(user_id: str, hashed_password: str) -> str:
    # Fingerprint ties the token to the current password, so it becomes invalid once used.
    return _encode(
        user_id,
        "reset",
        timedelta(minutes=get_settings().RESET_TOKEN_EXPIRE_MINUTES),
        {"fp": password_fingerprint(hashed_password)},
    )


def decode_token(token: str, expected_type: str) -> dict:
    """Raises jwt.PyJWTError on invalid/expired tokens or a wrong token type."""
    s = get_settings()
    payload = jwt.decode(token, s.JWT_SECRET, algorithms=[s.JWT_ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Wrong token type")
    return payload
