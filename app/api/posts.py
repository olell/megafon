from typing import Literal, Optional
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from datetime import datetime

from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.core.db import SessionDep
from app.models.crud import (
    flag_post,
    get_post_by_id,
    get_posts_by_timespan,
    create_post as crud_create_post,
    schedule_notifications,
    vote_post,
)
from app.models.models import BanMode, Post, PostCreate, PostWithChildren, Vote

router = APIRouter(prefix="/posts")


class VoteData(BaseModel):
    post: uuid.UUID
    value: Literal[-1, 0, 1]


class FlagData(BaseModel):
    post: uuid.UUID
    notice: str


@router.get("/info/{post_id}", response_model=PostWithChildren)
def get_post(*, session: SessionDep, post_id: uuid.UUID, user: CurrentUser):
    post = get_post_by_id(session, post_id)

    # Hide non-public posts from everyone but their author: admin-hidden posts,
    # and posts from ban-hidden / shadow-banned authors.
    author = post.created_by
    author_hidden = author is not None and author.ban_mode in (
        BanMode.BLOCKED_HIDDEN,
        BanMode.SHADOW,
    )
    if (post.hidden or author_hidden) and post.created_by_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found!"
        )

    return post


@router.get("/")
def get_posts(
    *,
    session: SessionDep,
    user: CurrentUser,
    since: Optional[datetime] = None,
    max_hours: int = 24,
    limit: int = 1000,
    order: Literal["votes", "newest"] = "newest",
) -> list[Post]:
    if since is None:
        since = datetime.now()

    posts = get_posts_by_timespan(
        session, since, max_hours, limit, order, viewer_id=user.id
    )
    return posts


@router.post("/")
def create_post(
    *,
    session: SessionDep,
    user: CurrentUser,
    data: PostCreate,
    background_tasks: BackgroundTasks,
):
    post = crud_create_post(session, user, data)
    background_tasks.add_task(schedule_notifications, post_id=post.id)
    return post


@router.post("/vote")
def vote(*, session: SessionDep, user: CurrentUser, data: VoteData):

    vote_post(session, user, data.post, data.value)

    return {"detail": "OK"}


@router.get("/votes")
def get_votes(*, session: SessionDep, user: CurrentUser) -> list[Vote]:
    return user.votes


@router.post("/flag")
def flag(*, session: SessionDep, user: CurrentUser, data: FlagData):
    flag_post(session, user, data.post, data.notice)
    return {"detail": "OK"}
