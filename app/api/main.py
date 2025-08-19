from fastapi import APIRouter

from app.api import posts
from app.api import user
from app.api import notify

router = APIRouter()
router.include_router(posts.router, tags=["posts"])
router.include_router(user.router, tags=["user"])
router.include_router(notify.router, tags=["notify"])
