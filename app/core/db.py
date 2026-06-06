from logging import getLogger
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

logger = getLogger(__name__)
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def init_db(session: Session) -> None:
    SQLModel.metadata.create_all(session.get_bind())
    logger.info("Created tables")


def drop_db(engine=engine) -> None:
    SQLModel.metadata.drop_all(engine)
    logger.info(f"Dropped all @ ({engine})")


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
