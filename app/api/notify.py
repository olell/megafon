from fastapi import APIRouter, Request
from pywebpush import webpush, WebPushException

from app.core.config import settings

router = APIRouter(prefix="/notify")

subscriptions = []
VAPID_CLAIMS = {"sub": "mailto:you@example.com"}


@router.get("/vapid_public_key")
def get_vapid_public_key():
    return {"publicKey": settings.NOTIFY_BASE64_PUBKEY}


@router.post("/subscribe")
async def subscribe(request: Request):
    subscription = await request.json()
    subscriptions.append(subscription)
    return {"status": "subscribed"}


def send_push_notification(message: str):
    for sub in subscriptions:
        try:
            webpush(
                subscription_info=sub,
                data=message,
                vapid_private_key=settings.NOTIFY_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
            )
        except WebPushException as ex:
            print("Push failed:", repr(ex))


@router.get("/")
async def post_message():
    send_push_notification("Hallo, dies ist ein Test!")
    return {"status": "ok"}
