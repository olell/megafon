"""Prometheus metrics endpoint.

Exposes only *aggregate* activity figures. By design it never emits post
content, usernames, user/post IDs, or push subscriptions — every series is a
count or a category bucket, so scraping this endpoint cannot reconstruct who
said what. Category labels (`ban_mode`, `subscription_mode`) are fixed enum
members, not free-form user data.

Metrics are recomputed from the database on each scrape via a custom collector,
so they reflect live state and survive process restarts (no in-memory drift).
"""

from datetime import datetime, timedelta
from logging import getLogger

from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.db import engine
from app.models.models import BanMode, Flag, Post, SubscriptionMode, User, Vote

logger = getLogger(__name__)

router = APIRouter()

# Rolling windows for "posts created in the last X" gauges. Votes carry no
# timestamp in the schema, so only posts can be windowed.
_WINDOWS = {"1h": timedelta(hours=1), "24h": timedelta(hours=24), "7d": timedelta(days=7)}


class MegafonCollector:
    """Queries the DB on every scrape and yields aggregate metric families."""

    def collect(self):
        with Session(engine) as session:

            def count(stmt) -> int:
                return int(session.exec(stmt).one())

            # --- Users -----------------------------------------------------
            yield GaugeMetricFamily(
                "megafon_users_total",
                "Total number of registered users.",
                value=count(select(func.count()).select_from(User)),
            )

            yield GaugeMetricFamily(
                "megafon_moderators_total",
                "Number of users with moderator privileges.",
                value=count(
                    select(func.count()).select_from(User).where(User.is_moderator)
                ),
            )

            # Banned users, bucketed by ban mode (category, not identity).
            banned = GaugeMetricFamily(
                "megafon_users_banned",
                "Number of users per ban mode.",
                labels=["mode"],
            )
            ban_counts = dict(
                session.exec(
                    select(User.ban_mode, func.count()).group_by(User.ban_mode)
                ).all()
            )
            for mode in BanMode:
                banned.add_metric([mode.value], float(ban_counts.get(mode, 0)))
            yield banned

            # Push-subscription opt-in, bucketed by subscription mode.
            subs = GaugeMetricFamily(
                "megafon_users_subscribed",
                "Number of users per push-subscription mode.",
                labels=["mode"],
            )
            sub_counts = dict(
                session.exec(
                    select(User.subscription_mode, func.count()).group_by(
                        User.subscription_mode
                    )
                ).all()
            )
            for mode in SubscriptionMode:
                subs.add_metric([mode.value], float(sub_counts.get(mode, 0)))
            yield subs

            # --- Posts -----------------------------------------------------
            posts = GaugeMetricFamily(
                "megafon_posts_total",
                "Number of posts, split into top-level posts and replies.",
                labels=["kind"],
            )
            posts.add_metric(
                ["post"],
                count(
                    select(func.count())
                    .select_from(Post)
                    .where(Post.parent_id.is_(None))
                ),
            )
            posts.add_metric(
                ["reply"],
                count(
                    select(func.count())
                    .select_from(Post)
                    .where(Post.parent_id.is_not(None))
                ),
            )
            yield posts

            yield GaugeMetricFamily(
                "megafon_posts_hidden_total",
                "Number of admin-hidden (soft-removed) posts.",
                value=count(
                    select(func.count()).select_from(Post).where(Post.hidden)
                ),
            )

            # Posts created within each rolling window.
            recent = GaugeMetricFamily(
                "megafon_posts_created_recent",
                "Posts (incl. replies) created within a rolling time window.",
                labels=["window"],
            )
            now = datetime.now()
            for label, delta in _WINDOWS.items():
                recent.add_metric(
                    [label],
                    count(
                        select(func.count())
                        .select_from(Post)
                        .where(Post.created_at >= now - delta)
                    ),
                )
            yield recent

            # --- Votes -----------------------------------------------------
            votes = GaugeMetricFamily(
                "megafon_votes_total",
                "Number of votes cast, split by direction.",
                labels=["direction"],
            )
            votes.add_metric(
                ["up"],
                count(select(func.count()).select_from(Vote).where(Vote.value == 1)),
            )
            votes.add_metric(
                ["down"],
                count(select(func.count()).select_from(Vote).where(Vote.value == -1)),
            )
            yield votes

            # --- Flags / moderation ---------------------------------------
            yield GaugeMetricFamily(
                "megafon_flags_total",
                "Total number of flag reports on record.",
                value=count(select(func.count()).select_from(Flag)),
            )
            yield GaugeMetricFamily(
                "megafon_flagged_posts_total",
                "Number of distinct posts that currently carry at least one flag.",
                value=count(select(func.count(func.distinct(Flag.post_id)))),
            )


# Dedicated registry so we expose *only* MEGAFON's aggregate series — no
# default process/GC/platform collectors leaking host details.
_registry = CollectorRegistry()
_registry.register(MegafonCollector())


@router.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(_registry), media_type=CONTENT_TYPE_LATEST)
