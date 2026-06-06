import json

from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from app.api.deps import CurrentUser
from app.core.config import settings
from app.core.db import SessionDep
from app.models.crud import subscribe_user
from app.models.models import SubscriptionMode

router = APIRouter(prefix="/notify")


class SubscribeData(BaseModel):
    subscription: str
    mode: SubscriptionMode

    @field_validator("subscription")
    @classmethod
    def subscription_must_be_json(cls, v: str) -> str:
        try:
            json.loads(v)
        except (json.JSONDecodeError, TypeError):
            raise ValueError("subscription must be a valid JSON string")
        return v


@router.get("/vapid_public_key")
def get_vapid_public_key():
    return {"publicKey": settings.NOTIFY_BASE64_PUBKEY}


@router.post("/subscribe")
async def subscribe(session: SessionDep, user: CurrentUser, data: SubscribeData):
    subscribe_user(session, user, data.subscription, data.mode)

    return {"detail": "OK"}
