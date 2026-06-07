from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Response
import jwt
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.core.db import SessionDep
from app.core.config import settings
from app.models.crud import create_user
from app.models.models import UserPublic

router = APIRouter(prefix="/user")


class SessionInit(BaseModel):
    username: str


@router.post("/")
def init_session(
    *, session: SessionDep, data: SessionInit, response: Response
) -> UserPublic:
    user = create_user(session, data.username)

    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    token = jwt.encode(
        {"sub": user.name, "uuid": str(user.id), "exp": expire},
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    response.set_cookie(
        key="auth",
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
    )
    return user


@router.get("/")
def get_session(*, session: SessionDep, user: CurrentUser) -> UserPublic:
    return user
