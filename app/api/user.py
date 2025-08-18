from fastapi import APIRouter, Response
import jwt
from pydantic import BaseModel

from app.core.db import SessionDep
from app.core.config import settings
from app.models.crud import create_user
from app.models.models import User

router = APIRouter(prefix="/user")


class SessionInit(BaseModel):
    username: str


@router.post("/")
def init_session(*, session: SessionDep, data: SessionInit, response: Response) -> User:
    user = create_user(session, data.username)

    token = jwt.encode(
        {"sub": user.name, "uuid": str(user.id)}, settings.SECRET_KEY, algorithm="HS256"
    )

    response.set_cookie(key="auth", value=token, expires=2147483647)
    return user
