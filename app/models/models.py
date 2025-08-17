import datetime
from typing import Literal, Optional, Self
import uuid
from sqlmodel import Field
from sqlmodel import Relationship, SQLModel
from datetime import datetime


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str

    posts: list["Post"] = Relationship(back_populates="created_by")
    created_flags: list["Flag"] = Relationship(back_populates="created_by")


class Post(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    created_at: datetime = Field(default_factory=datetime.now)

    created_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    created_by: Optional[User] = Relationship(back_populates="posts")

    ref_id: Optional[uuid.UUID] = Field(default=None, foreign_key="post.id")
    ref: Optional[Self] = Relationship(back_populates="refering")

    content: str

    votes: list["Vote"] = Relationship(back_populates="post")
    flags: list["Flag"] = Relationship(back_populates="post")
    refering: list["Post"] = Relationship(back_populates="ref")


class Vote(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    value: int = Field(le=1, ge=-1)

    post_id: Optional[uuid.UUID] = Field(default=None, foreign_key="post.id")
    post: Optional[Post] = Relationship(back_populates="votes")

    created_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    created_by: Optional[User] = Relationship(back_populates="votes")


class Flag(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    post_id: Optional[uuid.UUID] = Field(default=None, foreign_key="post.id")
    post: Optional[Post] = Relationship(back_populates="flags")

    created_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    created_by: Optional[User] = Relationship(back_populates="created_flags")

    notice: Optional[str] = None
