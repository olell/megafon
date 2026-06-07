from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie
import jwt

from app.core.config import settings
from app.core.db import SessionDep
from app.core.security import decode_admin_token
from app.models.crud import get_user_by_id
from app.models.models import BanMode, User

# Optional cookie schemes (no auto 403 when absent) used by the moderator
# dependency, which has to consider two possible credentials.
_optional_admin_cookie = APIKeyCookie(name="admin_auth", auto_error=False)
_optional_user_cookie = APIKeyCookie(name="auth", auto_error=False)


def get_current_user(
    session: SessionDep,
    token: str = Depends(APIKeyCookie(name="auth")),
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated!"
        )

    user = get_user_by_id(session, payload.get("uuid"))

    # Blocked users can't perform authenticated actions. Shadow-banned users
    # pass through here on purpose — they must never notice the ban.
    if user.ban_mode in (BanMode.BLOCKED, BanMode.BLOCKED_HIDDEN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated!"
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_admin(
    token: str = Depends(APIKeyCookie(name="admin_auth")),
) -> bool:
    if not decode_admin_token(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated!"
        )
    return True


AdminDep = Annotated[bool, Depends(get_current_admin)]


def get_moderator(
    session: SessionDep,
    admin_token: Optional[str] = Depends(_optional_admin_cookie),
    user_token: Optional[str] = Depends(_optional_user_cookie),
) -> str:
    """Allow either the root admin or a promoted moderator user. Returns the
    caller's role ('admin' or 'moderator'); raises 403 for anyone else."""
    if admin_token and decode_admin_token(admin_token):
        return "admin"

    if user_token:
        try:
            payload = jwt.decode(user_token, settings.SECRET_KEY, algorithms=["HS256"])
            user = get_user_by_id(session, payload.get("uuid"))
        except (jwt.PyJWTError, HTTPException):
            user = None
        if (
            user is not None
            and user.is_moderator
            and user.ban_mode not in (BanMode.BLOCKED, BanMode.BLOCKED_HIDDEN)
        ):
            return "moderator"

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated!"
    )


ModeratorDep = Annotated[str, Depends(get_moderator)]
