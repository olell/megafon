import datetime
from enum import Enum
from typing import Dict, Literal, Optional, Self
import uuid
from pydantic import BaseModel, computed_field
from sqlmodel import JSON, Column, Field
from sqlmodel import Relationship, SQLModel
from datetime import datetime


class SubscriptionMode(Enum):
    NONE = "none"
    USER = "user"
    ALL = "all"
    GLOBAL = "global"


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str

    votes: list["Vote"] = Relationship(back_populates="created_by")
    posts: list["Post"] = Relationship(back_populates="created_by")
    created_flags: list["Flag"] = Relationship(back_populates="created_by")

    subscription: str = Field(default="{}", max_length=1024)
    subscription_mode: SubscriptionMode = SubscriptionMode.NONE


class Post(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    created_at: datetime = Field(default_factory=datetime.now)

    created_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    created_by: Optional[User] = Relationship(back_populates="posts")

    parent_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="post.id", nullable=True
    )
    parent: Optional["Post"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs=dict(remote_side="Post.id"),
    )

    @computed_field
    @property
    def created_by_name(self) -> str:
        return self.created_by.name

    @computed_field
    @property
    def upvotes(self) -> int:
        return len([v for v in self.votes if v.value == 1])

    @computed_field
    @property
    def downvotes(self) -> int:
        return len([v for v in self.votes if v.value == -1])

    @computed_field
    @property
    def children_count(self) -> int:
        return sum([c.children_count for c in self.children]) + len(self.children)

    content: str

    votes: list["Vote"] = Relationship(back_populates="post")
    flags: list["Flag"] = Relationship(back_populates="post")
    children: list["Post"] = Relationship(back_populates="parent")


class PostWithChildren(BaseModel):
    id: uuid.UUID
    created_at: datetime
    content: str
    parent_id: Optional[uuid.UUID]
    created_by_name: str
    upvotes: int
    downvotes: int
    children_count: int
    children: list["PostWithChildren"] = []


PostWithChildren.model_rebuild()


class PostCreate(BaseModel):
    parent: Optional[uuid.UUID] = None
    content: str


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
