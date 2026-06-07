import secrets
from typing import Literal, Optional
import uuid

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel

from app.api.deps import AdminDep, ModeratorDep
from app.core.config import settings
from app.core.db import SessionDep
from app.core.security import create_admin_token, verify_root_password
from app.models.crud import (
    compute_stats,
    delete_post_cascade,
    dismiss_flags,
    list_all_posts,
    list_flagged_posts,
    list_users_with_stats,
    set_post_hidden,
    set_user_ban,
    set_user_moderator,
)
from app.models.models import (
    AdminFlagItem,
    AdminPostItem,
    AdminStats,
    AdminUserItem,
    BanMode,
)

router = APIRouter(prefix="/admin")

ADMIN_COOKIE = "admin_auth"


class AdminLogin(BaseModel):
    username: str
    password: str


class BanData(BaseModel):
    mode: BanMode


class ModeratorData(BaseModel):
    is_moderator: bool


class SessionInfo(BaseModel):
    role: Literal["admin", "moderator"]


@router.post("/login")
def admin_login(*, data: AdminLogin, response: Response):
    # Constant-time username compare + argon2 password verify; a single generic
    # error for any failure avoids leaking which part was wrong.
    user_ok = secrets.compare_digest(data.username, settings.DEFAULT_ROOT_USER)
    pw_ok = verify_root_password(data.password)
    if not (user_ok and pw_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials!"
        )

    token = create_admin_token()
    response.set_cookie(
        key=ADMIN_COOKIE,
        value=token,
        max_age=settings.ADMIN_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax",
    )
    return {"detail": "OK"}


@router.post("/logout")
def admin_logout(response: Response):
    response.delete_cookie(ADMIN_COOKIE)
    return {"detail": "OK"}


@router.get("/session")
def admin_session(*, role: ModeratorDep) -> SessionInfo:
    return SessionInfo(role=role)


# --- Flag moderation: available to the root admin AND promoted moderators ---


@router.get("/flags")
def admin_flags(*, session: SessionDep, role: ModeratorDep) -> list[AdminFlagItem]:
    return list_flagged_posts(session)


@router.post("/flags/{post_id}/dismiss")
def admin_dismiss_flags(*, session: SessionDep, role: ModeratorDep, post_id: uuid.UUID):
    dismiss_flags(session, post_id)
    return {"detail": "OK"}


@router.post("/posts/{post_id}/hide")
def admin_hide_post(*, session: SessionDep, role: ModeratorDep, post_id: uuid.UUID):
    set_post_hidden(session, post_id, True)
    return {"detail": "OK"}


@router.post("/posts/{post_id}/unhide")
def admin_unhide_post(*, session: SessionDep, role: ModeratorDep, post_id: uuid.UUID):
    set_post_hidden(session, post_id, False)
    return {"detail": "OK"}


@router.delete("/posts/{post_id}")
def admin_delete_post(*, session: SessionDep, role: ModeratorDep, post_id: uuid.UUID):
    delete_post_cascade(session, post_id)
    return {"detail": "OK"}


@router.get("/users")
def admin_users(
    *, session: SessionDep, admin: AdminDep, search: Optional[str] = None
) -> list[AdminUserItem]:
    return list_users_with_stats(session, search)


@router.post("/users/{user_id}/ban")
def admin_ban_user(
    *, session: SessionDep, admin: AdminDep, user_id: uuid.UUID, data: BanData
):
    set_user_ban(session, user_id, data.mode)
    return {"detail": "OK"}


@router.post("/users/{user_id}/moderator")
def admin_set_moderator(
    *, session: SessionDep, admin: AdminDep, user_id: uuid.UUID, data: ModeratorData
):
    # Root-only: grant or revoke flag-moderation access for a user.
    set_user_moderator(session, user_id, data.is_moderator)
    return {"detail": "OK"}


@router.get("/posts")
def admin_posts(
    *,
    session: SessionDep,
    admin: AdminDep,
    limit: int = 100,
    offset: int = 0,
    include_hidden: bool = True,
    user_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
) -> list[AdminPostItem]:
    return list_all_posts(session, limit, offset, include_hidden, user_id, search)


@router.get("/stats")
def admin_stats(*, session: SessionDep, admin: AdminDep) -> AdminStats:
    return compute_stats(session)
