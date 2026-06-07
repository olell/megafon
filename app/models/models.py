import datetime
from enum import Enum
from typing import Dict, Literal, Optional, Self
import uuid
from pydantic import BaseModel, computed_field
from sqlalchemy import UniqueConstraint
from sqlmodel import JSON, Column, Field
from sqlmodel import Relationship, SQLModel
from datetime import datetime


class SubscriptionMode(Enum):
    NONE = "none"
    USER = "user"
    ALL = "all"
    GLOBAL = "global"


class BanMode(str, Enum):
    NONE = "none"
    # Can't perform authenticated actions; existing content stays visible.
    BLOCKED = "blocked"
    # Can't perform authenticated actions; existing content hidden from the feed.
    BLOCKED_HIDDEN = "blocked_hidden"
    # Acts normally and never notices, but content is hidden from everyone else
    # while remaining visible to the user themselves.
    SHADOW = "shadow"


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str

    votes: list["Vote"] = Relationship(back_populates="created_by")
    posts: list["Post"] = Relationship(back_populates="created_by")
    created_flags: list["Flag"] = Relationship(back_populates="created_by")

    subscription: str = Field(default="{}", max_length=1024)
    subscription_mode: SubscriptionMode = SubscriptionMode.NONE

    ban_mode: BanMode = Field(default=BanMode.NONE)
    # Grants access to the admin panel's flag-moderation section only.
    is_moderator: bool = Field(default=False)


class UserPublic(BaseModel):
    """Session payload. Deliberately omits `ban_mode` (a shadow-banned user must
    not learn they're banned) and the raw push `subscription`."""

    id: uuid.UUID
    name: str
    is_moderator: bool


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
        return self.created_by.name if self.created_by else "anonymous"

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

    # Admin soft-hide: kept in the DB / history but removed from the public feed.
    hidden: bool = Field(default=False)

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
    __table_args__ = (UniqueConstraint("created_by_id", "post_id"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    value: int = Field(le=1, ge=-1)

    post_id: Optional[uuid.UUID] = Field(default=None, foreign_key="post.id")
    post: Optional[Post] = Relationship(back_populates="votes")

    created_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    created_by: Optional[User] = Relationship(back_populates="votes")


class Event(SQLModel, table=True):
    # Append-only feed log driving SSE. The autoincrement id is the monotonic
    # cursor handed to clients as Last-Event-ID. post_id is a plain UUID (NOT a
    # foreign key) so the admin cascade delete never trips on dangling log rows.
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    kind: str  # "post" | "vote" | "flag"
    post_id: Optional[uuid.UUID] = Field(default=None)


class Flag(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("created_by_id", "post_id"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    post_id: Optional[uuid.UUID] = Field(default=None, foreign_key="post.id")
    post: Optional[Post] = Relationship(back_populates="flags")

    created_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    created_by: Optional[User] = Relationship(back_populates="created_flags")

    notice: Optional[str] = None


# ============================================================================
#  ADMIN RESPONSE SCHEMAS (read-only; never persisted)
# ============================================================================


class AdminFlagReport(BaseModel):
    reporter: str
    notice: Optional[str]


class AdminFlagItem(BaseModel):
    id: uuid.UUID
    content: str
    created_by_name: str
    created_at: datetime
    parent_id: Optional[uuid.UUID]
    hidden: bool
    upvotes: int
    downvotes: int
    reports: list[AdminFlagReport]


class AdminUserItem(BaseModel):
    id: uuid.UUID
    name: str
    ban_mode: BanMode
    is_moderator: bool
    subscription_mode: SubscriptionMode
    post_count: int
    flags_received: int


class AdminPostItem(BaseModel):
    id: uuid.UUID
    content: str
    created_by_name: str
    created_by_id: Optional[uuid.UUID]
    created_at: datetime
    parent_id: Optional[uuid.UUID]
    hidden: bool
    upvotes: int
    downvotes: int
    flag_count: int


class AdminActivityPoint(BaseModel):
    day: str
    posts: int
    votes: int


class AdminTopPoster(BaseModel):
    name: str
    post_count: int


class AdminTopPost(BaseModel):
    id: uuid.UUID
    content: str
    created_by_name: str
    score: int


class AdminStats(BaseModel):
    # Totals
    total_users: int
    total_posts: int
    total_replies: int
    total_votes: int
    active_flags: int
    # Moderation metrics
    hidden_posts: int
    banned_users: int
    # Activity over time (per day) + top contributors
    activity: list[AdminActivityPoint]
    top_posters: list[AdminTopPoster]
    top_posts: list[AdminTopPost]
