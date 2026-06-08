from datetime import datetime, timedelta, timezone
import hashlib
from typing import Literal
from fastapi import APIRouter, Response
import jwt
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.core.avatar import identicon_svg
from app.core.db import SessionDep
from app.core.config import settings
from app.models.crud import create_user, search_usernames
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


@router.get("/search")
def search_users(
    *, session: SessionDep, user: CurrentUser, q: str, limit: int = 8
) -> list[str]:
    return search_usernames(session, q, limit)


@router.get("/avatar/{seed}")
def user_avatar(*, seed: str, theme: Literal["light", "dark"] = "light") -> Response:
    # Public + unauthenticated so plain <img> tags work. The output is a pure,
    # deterministic function of (seed, theme) and exposes nothing about the user,
    # so it caches forever (the avatar for a given seed/theme never changes).
    dark = theme == "dark"
    return Response(
        content=identicon_svg(seed, dark),
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "ETag": '"' + hashlib.sha256(f"{theme}:{seed}".encode()).hexdigest()[:16] + '"',
        },
    )
