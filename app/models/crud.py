from datetime import datetime, timedelta
from typing import Literal
import uuid
from fastapi import HTTPException, status
import sqlalchemy
from sqlmodel import Session, select

from app.models.models import Flag, Post, PostCreate, User, Vote
from sqlalchemy import func


def create_user(session: Session, username: str) -> User:
    user = User(name=username)
    session.add(user)
    session.commit()
    session.refresh(user)

    return user


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
) -> list[Post]:
    start_time = since - timedelta(hours=max_hours)
    query = (
        select(Post)
        .where(Post.created_at < since, Post.created_at >= start_time)
        .where(Post.parent_id.is_(None))
        .where(~Post.flags.any())
    )

    if order == "votes":
        query = (
            query.outerjoin(Vote, Vote.post_id == Post.id)
            .group_by(Post.id)
            .order_by(func.coalesce(func.sum(Vote.value), 0).desc())
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
        session.commit()
        session.refresh(flag)
        return flag
    except:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Failed to report!"
        )
