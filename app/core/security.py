"""Admin authentication helpers.

The regular user session is passwordless (a username -> JWT in the `auth`
cookie). The admin area is gated by the root credentials from settings and a
separate, short-lived `admin_auth` JWT so the two sessions never collide.
"""

from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error

from app.core.config import settings

_ph = PasswordHasher()


def verify_root_password(plain: str) -> bool:
    """Verify a plaintext password against the configured argon2 hash."""
    try:
        return _ph.verify(settings.DEFAULT_ROOT_PASSWORD, plain)
    except Argon2Error:
        return False


def create_admin_token() -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ADMIN_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"role": "admin", "sub": settings.DEFAULT_ROOT_USER, "exp": expire},
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def decode_admin_token(token: str) -> bool:
    """Return True iff the token is a valid, unexpired admin token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        return False
    return payload.get("role") == "admin"
