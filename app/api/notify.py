from fastapi import APIRouter, Request
from pydantic import BaseModel
from pywebpush import webpush, WebPushException

from app.api.deps import CurrentUser
from app.core.config import settings
from app.core.db import SessionDep
from app.models.crud import subscribe_user
from app.models.models import SubscriptionMode

router = APIRouter(prefix="/notify")

subscriptions = []
VAPID_CLAIMS = {"sub": "mailto:you@example.com"}


class SubscribeData(BaseModel):
    subscription: str
    mode: SubscriptionMode


@router.get("/vapid_public_key")
def get_vapid_public_key():
    return {"publicKey": settings.NOTIFY_BASE64_PUBKEY}


@router.post("/subscribe")
async def subscribe(session: SessionDep, user: CurrentUser, data: SubscribeData):
    subscribe_user(session, user, data.subscription, data.mode)

    return {"detail": "OK"}
