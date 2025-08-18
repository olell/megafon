from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie
import jwt

from app.core.config import settings
from app.core.db import SessionDep
from app.models.crud import get_user_by_id
from app.models.models import User


def get_current_user(
    session: SessionDep,
    token: str = Depends(APIKeyCookie(name="auth")),
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return get_user_by_id(session, payload.get("uuid"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated!"
        )


CurrentUser = Annotated[User, Depends(get_current_user)]
