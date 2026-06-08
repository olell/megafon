from datetime import datetime, timedelta
import json
from logging import getLogger
import re
from typing import Literal, Optional
import uuid
from fastapi import HTTPException, status
from py_vapid import Vapid
from pywebpush import webpush, WebPushException
import sqlalchemy
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine
from app.models.models import (
    AdminActivityPoint,
    AdminFlagItem,
    AdminFlagReport,
    AdminPostItem,
    AdminStats,
    AdminTopPost,
    AdminTopPoster,
    AdminUserItem,
    BanMode,
    Event,
    Flag,
    Post,
    PostCreate,
    SubscriptionMode,
    User,
    Vote,
)
from sqlalchemy import func, or_

logger = getLogger(__name__)

# pywebpush only accepts a PEM via a Vapid object (a PEM *string* is run through
# Vapid.from_string, which base64-decodes it and fails). Build it once here.
vapid = Vapid.from_pem(settings.NOTIFY_PRIVATE_KEY.encode())


def create_user(session: Session, username: str) -> User:
    user = User(name=username)
    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def search_usernames(session: Session, q: str, limit: int = 8) -> list[str]:
    """Prefix-match usernames for @mention autocomplete. Names are deduped
    (the same name can be registered by several users) and kick in from the
    first character."""
    q = q.strip()
    if len(q) < 1:
        return []
    names = list(
        session.exec(
            select(User.name)
            .where(User.name.ilike(f"{q}%"))
            .distinct()
            .order_by(User.name)
            .limit(limit)
        ).all()
    )
    # "@all" is a broadcast pseudo-mention handled in schedule_notifications;
    # surface it as a completion (first) when it matches the prefix.
    if "all".startswith(q.lower()) and "all" not in names:
        names.insert(0, "all")
        names = names[:limit]
    return names


def subscribe_user(
    session: Session, user: User, subscription: str, mode: SubscriptionMode
):
    user.subscription = subscription
    user.subscription_mode = mode
    session.add(user)
    session.commit()

    logger.info("Subscribed user %s (%s)", user.name, mode)


def schedule_notifications(post_id: uuid.UUID):
    # Runs as a background task after the request's session is already closed,
    # so open a fresh session and re-load the post here.
    with Session(engine) as session:
        post = session.get(Post, post_id)
        if post is None:
            return

        all_users = session.exec(select(User)).all()

        content = post.content.lower()
        at_all = "@all" in content

        # A reply notifies the parent post's author directly (any mode except
        # NONE), independent of @mentions. Skip self-replies.
        reply_target_id = None
        if post.parent_id is not None:
            parent = session.get(Post, post.parent_id)
            if (
                parent is not None
                and parent.created_by_id is not None
                and parent.created_by_id != post.created_by_id
            ):
                reply_target_id = parent.created_by_id

        logger.info("Scheduled notifications for %s", content)

        for user in all_users:
            if user.subscription_mode == SubscriptionMode.NONE:
                continue

            # Word-boundary match so "tom" doesn't match "tomato" and short
            # names don't match every post.
            at_user = (
                re.search(rf"(?<!\w){re.escape(user.name.lower())}(?!\w)", content)
                is not None
            )

            do_notify = False
            if user.subscription_mode == SubscriptionMode.GLOBAL:
                do_notify = True
            elif user.subscription_mode == SubscriptionMode.ALL:
                do_notify = at_user or at_all
            elif user.subscription_mode == SubscriptionMode.USER:
                do_notify = at_user

            # The reply signal forces a notification and its more specific
            # message wins, so the parent author is never double-notified when
            # an @all / global rule would also have matched.
            is_reply_target = user.id == reply_target_id
            if is_reply_target:
                do_notify = True

            logger.debug(
                "Notify %s: %s (mention=%s, all=%s, reply=%s)",
                user.name,
                do_notify,
                at_user,
                at_all,
                is_reply_target,
            )
            if not do_notify:
                continue

            if is_reply_target:
                message = f"{post.created_by_name} replied: {post.content}"
            else:
                message = f"{post.created_by_name}: {post.content}"
            push_notification(user, message)


def push_notification(user: User, message: str):
    if user.subscription == "{}" or user.subscription_mode == SubscriptionMode.NONE:
        return

    try:
        webpush(
            subscription_info=json.loads(user.subscription),
            data=message,
            vapid_private_key=vapid,
            vapid_claims={"sub": "mailto:megafon@example.com"},
        )
    except WebPushException as ex:
        logger.warning("Push failed: %r", ex)


def record_event(session: Session, kind: str, post_id: Optional[uuid.UUID]) -> None:
    """Append a feed event. Added to the caller's transaction so it commits
    atomically with the write it describes; SSE streams poll these rows."""
    session.add(Event(kind=kind, post_id=post_id))


def get_user_by_id(session: Session, user_id: str) -> User:
    user = session.exec(select(User).where(User.id == uuid.UUID(user_id))).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found!"
        )
    return user


def get_post_by_id(session: Session, post_id: str) -> Post:
    post = session.exec(select(Post).where(Post.id == post_id)).first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found!"
        )
    return post


def get_posts_by_timespan(
    session: Session,
    since: datetime,
    max_hours: int,
    limit: int,
    order: Literal["votes", "newest"],
    viewer_id: Optional[uuid.UUID] = None,
) -> list[Post]:
    start_time = since - timedelta(hours=max_hours)
    query = (
        select(Post)
        .where(Post.created_at < since, Post.created_at >= start_time)
        .where(Post.parent_id.is_(None))
        .where(~Post.flags.any())  # flagged posts stay auto-hidden
        .where(~Post.hidden)  # admin soft-hide
        # Hide content from ban-hidden / shadow-banned authors, but let a
        # shadow-banned viewer still see their own posts (they must not notice).
        .join(User, Post.created_by_id == User.id)
        .where(
            or_(
                User.ban_mode.notin_([BanMode.BLOCKED_HIDDEN, BanMode.SHADOW]),
                User.id == viewer_id,
            )
        )
    )

    if order == "votes":
        query = (
            query.outerjoin(Vote, Vote.post_id == Post.id)
            .group_by(Post.id)
            .order_by(
                func.coalesce(func.sum(Vote.value), 0).desc(), Post.created_at.desc()
            )
        )
    elif order == "newest":
        query = query.order_by(Post.created_at.desc())

    posts = session.exec(query.limit(limit)).all()
    return posts


def create_post(session: Session, user: User, data: PostCreate) -> Post:
    if len(data.content.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Content too short!"
        )

    try:
        post = Post(
            created_by_id=user.id,
            parent_id=data.parent,
            content=data.content,
        )
        session.add(post)
        record_event(session, "post", post.id)
        session.commit()
        session.refresh(post)
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Failed to post!"
        )

    return post


def vote_post(session: Session, user: User, post: uuid.UUID, value: Literal[-1, 0, 1]):
    vote = session.exec(
        select(Vote).where(Vote.created_by_id == user.id).where(Vote.post_id == post)
    ).first()

    if value == 0 and vote:
        session.delete(vote)
        record_event(session, "vote", post)
        session.commit()
        return
    elif value == 0:
        return

    try:
        if vote:
            vote.value = value
        else:
            vote = Vote(post_id=post, value=value, created_by_id=user.id)

        session.add(vote)
        record_event(session, "vote", post)
        session.commit()
        session.refresh(vote)

    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Failed to vote!"
        )

    return vote


def flag_post(session: Session, user: User, post: uuid.UUID, notice: str):
    flag = session.exec(
        select(Flag).where(Flag.created_by_id == user.id).where(Flag.post_id == post)
    ).first()
    if flag:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You've already reported this post!",
        )

    try:
        flag = Flag(post_id=post, created_by_id=user.id, notice=notice)
        session.add(flag)
        record_event(session, "flag", post)
        session.commit()
        session.refresh(flag)
        return flag
    except sqlalchemy.exc.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Failed to report!"
        )


def update_post(session: Session, user: User, post_id: uuid.UUID, content: str) -> Post:
    """Edit the content of a post the caller owns. A reported post is locked so it
    stays intact for moderation. Records a feed event so SSE clients refresh."""
    post = get_post_by_id(session, post_id)

    # Mirror the visibility 404 from the API: never reveal someone else's post.
    if post.created_by_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found!"
        )
    if post.flags:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Post has been reported and can't be edited!",
        )
    if len(content.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Content too short!"
        )

    post.content = content
    post.edited_at = datetime.now()
    session.add(post)
    record_event(session, "post", post.id)
    session.commit()
    session.refresh(post)
    return post


def delete_own_post(session: Session, user: User, post_id: uuid.UUID) -> None:
    """Delete a post the caller owns, cascading to its replies, votes and flags.
    A reported post is locked so it stays intact for moderation."""
    post = get_post_by_id(session, post_id)

    if post.created_by_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found!"
        )
    if post.flags:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Post has been reported and can't be deleted!",
        )

    # Recorded before the cascade (which commits) so other clients' feeds refresh.
    record_event(session, "post", post_id)
    delete_post_cascade(session, post_id)


# ============================================================================
#  ADMIN
# ============================================================================


def list_flagged_posts(session: Session) -> list[AdminFlagItem]:
    """All posts that currently carry at least one flag, with report details."""
    posts = session.exec(select(Post).where(Post.flags.any())).all()
    posts.sort(key=lambda p: len(p.flags), reverse=True)
    return [
        AdminFlagItem(
            id=p.id,
            content=p.content,
            created_by_name=p.created_by_name,
            created_at=p.created_at,
            parent_id=p.parent_id,
            hidden=p.hidden,
            upvotes=p.upvotes,
            downvotes=p.downvotes,
            reports=[
                AdminFlagReport(
                    reporter=f.created_by.name if f.created_by else "anonymous",
                    notice=f.notice,
                )
                for f in p.flags
            ],
        )
        for p in posts
    ]


def dismiss_flags(session: Session, post_id: uuid.UUID) -> Post:
    """Delete all flags on a post, restoring it to the feed."""
    post = get_post_by_id(session, post_id)
    for flag in list(post.flags):
        session.delete(flag)
    session.commit()
    session.refresh(post)
    return post


def set_post_hidden(session: Session, post_id: uuid.UUID, hidden: bool) -> Post:
    post = get_post_by_id(session, post_id)
    post.hidden = hidden
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


def delete_post_cascade(session: Session, post_id: uuid.UUID) -> None:
    """Permanently delete a post plus its votes, flags and replies.

    No DB-level cascade is configured, so children are removed recursively.
    """
    post = get_post_by_id(session, post_id)
    for child in list(post.children):
        delete_post_cascade(session, child.id)
    for vote in list(post.votes):
        session.delete(vote)
    for flag in list(post.flags):
        session.delete(flag)
    session.delete(post)
    session.commit()


def list_users_with_stats(
    session: Session, search: Optional[str] = None
) -> list[AdminUserItem]:
    query = select(User)
    if search:
        query = query.where(User.name.ilike(f"%{search}%"))
    users = session.exec(query).all()
    return [
        AdminUserItem(
            id=u.id,
            name=u.name,
            ban_mode=u.ban_mode,
            is_moderator=u.is_moderator,
            subscription_mode=u.subscription_mode,
            post_count=len(u.posts),
            flags_received=sum(len(p.flags) for p in u.posts),
        )
        for u in sorted(users, key=lambda u: len(u.posts), reverse=True)
    ]


def set_user_ban(session: Session, user_id: uuid.UUID, mode: BanMode) -> User:
    user = get_user_by_id(session, str(user_id))
    user.ban_mode = mode
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def set_user_moderator(session: Session, user_id: uuid.UUID, value: bool) -> User:
    user = get_user_by_id(session, str(user_id))
    user.is_moderator = value
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def list_all_posts(
    session: Session,
    limit: int = 100,
    offset: int = 0,
    include_hidden: bool = True,
    user_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
) -> list[AdminPostItem]:
    """Full message history: every post (top-level and replies), newest first."""
    query = select(Post)
    if not include_hidden:
        query = query.where(~Post.hidden)
    if user_id is not None:
        query = query.where(Post.created_by_id == user_id)
    if search:
        query = query.where(Post.content.ilike(f"%{search}%"))
    query = query.order_by(Post.created_at.desc()).limit(limit).offset(offset)
    posts = session.exec(query).all()
    return [
        AdminPostItem(
            id=p.id,
            content=p.content,
            created_by_name=p.created_by_name,
            created_by_id=p.created_by_id,
            created_at=p.created_at,
            parent_id=p.parent_id,
            hidden=p.hidden,
            upvotes=p.upvotes,
            downvotes=p.downvotes,
            flag_count=len(p.flags),
        )
        for p in posts
    ]


def compute_stats(session: Session) -> AdminStats:
    total_users = session.exec(select(func.count()).select_from(User)).one()
    total_posts = session.exec(
        select(func.count()).select_from(Post).where(Post.parent_id.is_(None))
    ).one()
    total_replies = session.exec(
        select(func.count()).select_from(Post).where(Post.parent_id.is_not(None))
    ).one()
    total_votes = session.exec(select(func.count()).select_from(Vote)).one()
    active_flags = session.exec(
        select(func.count(func.distinct(Flag.post_id)))
    ).one()
    hidden_posts = session.exec(
        select(func.count()).select_from(Post).where(Post.hidden)
    ).one()
    banned_users = session.exec(
        select(func.count()).select_from(User).where(User.ban_mode != BanMode.NONE)
    ).one()

    # Activity over the last 30 days, bucketed per calendar day.
    cutoff = datetime.now() - timedelta(days=30)
    posts_by_day = dict(
        session.exec(
            select(func.date(Post.created_at), func.count())
            .where(Post.created_at >= cutoff)
            .group_by(func.date(Post.created_at))
        ).all()
    )
    votes_by_day: dict = {}  # Vote has no created_at; left empty intentionally.
    days = sorted(set(posts_by_day) | set(votes_by_day))
    activity = [
        AdminActivityPoint(
            day=str(d),
            posts=int(posts_by_day.get(d, 0)),
            votes=int(votes_by_day.get(d, 0)),
        )
        for d in days
    ]

    top_posters = [
        AdminTopPoster(name=name, post_count=int(count))
        for name, count in session.exec(
            select(User.name, func.count(Post.id))
            .join(Post, Post.created_by_id == User.id)
            .group_by(User.id)
            .order_by(func.count(Post.id).desc())
            .limit(10)
        ).all()
    ]

    top_post_rows = session.exec(
        select(Post.id, func.coalesce(func.sum(Vote.value), 0).label("score"))
        .outerjoin(Vote, Vote.post_id == Post.id)
        .group_by(Post.id)
        .order_by(func.coalesce(func.sum(Vote.value), 0).desc())
        .limit(10)
    ).all()
    top_posts = []
    for post_id, score in top_post_rows:
        post = session.get(Post, post_id)
        if post is None:
            continue
        top_posts.append(
            AdminTopPost(
                id=post.id,
                content=post.content,
                created_by_name=post.created_by_name,
                score=int(score),
            )
        )

    return AdminStats(
        total_users=int(total_users),
        total_posts=int(total_posts),
        total_replies=int(total_replies),
        total_votes=int(total_votes),
        active_flags=int(active_flags),
        hidden_posts=int(hidden_posts),
        banned_users=int(banned_users),
        activity=activity,
        top_posters=top_posters,
        top_posts=top_posts,
    )
