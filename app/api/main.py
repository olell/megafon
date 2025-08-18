from fastapi import APIRouter

from app.api import posts
from app.api import user

router = APIRouter()
router.include_router(posts.router, tags=["posts"])
router.include_router(user.router, tags=["user"])
