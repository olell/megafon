from fastapi import APIRouter

from app.api import posts
from app.api import user
from app.api import notify
from app.api import admin

router = APIRouter()
router.include_router(posts.router, tags=["posts"])
router.include_router(user.router, tags=["user"])
router.include_router(notify.router, tags=["notify"])
router.include_router(admin.router, tags=["admin"])
