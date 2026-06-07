import asyncio
from typing import Literal, Optional
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from app.api.deps import CurrentUser
from app.core.db import SessionDep, engine
from app.models.crud import (
    flag_post,
    get_post_by_id,
    get_posts_by_timespan,
    create_post as crud_create_post,
    schedule_notifications,
    vote_post,
)
from app.models.models import BanMode, Event, Post, PostCreate, PostWithChildren, Vote

router = APIRouter(prefix="/posts")

# How often each SSE stream polls the event log for new rows.
STREAM_POLL_SECONDS = 1.5


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


@router.get("/stream")
async def stream(request: Request, user: CurrentUser):
    """Server-Sent Events feed. Streams new post/vote/flag events so clients can
    refresh instead of polling. Auth is the normal `auth` cookie via CurrentUser.

    The event id is the autoincrement Event.id; the browser's EventSource sends
    it back as Last-Event-ID on reconnect, so missed events replay automatically.
    """
    last_id_hdr = request.headers.get("last-event-id")

    async def gen():
        # No Last-Event-ID (fresh connect): start at the current max id and emit
        # only future events — the client already loaded the feed via the REST
        # endpoint, so there's nothing to replay.
        with Session(engine) as s:
            if last_id_hdr and last_id_hdr.isdigit():
                cursor = int(last_id_hdr)
            else:
                cursor = s.exec(select(func.coalesce(func.max(Event.id), 0))).one()

        yield ": connected\n\n"

        while not await request.is_disconnected():
            with Session(engine) as s:
                rows = s.exec(
                    select(Event).where(Event.id > cursor).order_by(Event.id)
                ).all()

            if rows:
                for ev in rows:
                    cursor = ev.id
                    yield f"id: {ev.id}\nevent: {ev.kind}\ndata: {ev.post_id}\n\n"
            else:
                # Heartbeat: keeps proxies from closing the idle connection and
                # lets the server notice a dropped client on the next write.
                yield ": ping\n\n"

            await asyncio.sleep(STREAM_POLL_SECONDS)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
