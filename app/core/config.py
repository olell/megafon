from logging import INFO, getLevelNamesMapping
import secrets
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BaseModel,
    BeforeValidator,
    computed_field,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class PublicSettings(BaseModel): ...


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
        env_prefix="MEGAFON_",
    )

    ## SECURITY

    DEFAULT_ROOT_USER: str = "root"
    DEFAULT_ROOT_PASSWORD: str = (
        "$argon2i$v=19$m=16,t=2,p=1$Nk9LTEFLRmtWYUExTXVVZw$5JDkSZaDa89JoVSoe6UiUQ"
    )

    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520  # 8 days

    ## NETWORK
    API_V1_STR: str = "/api/v1"

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = (
        []
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS]

    ## DATABASE
    DATABASE_TYPE: Literal["mysql"] | Literal["postgres"] = "postgres"
    DATABASE_SERVER: str
    DATABASE_PORT: int = 5432
    DATABASE_USER: str
    DATABASE_PASSWORD: str = ""
    DATABASE_DB: str = ""

    LIFESPAN_DROP_DB: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return str(
            MultiHostUrl.build(
                scheme=(
                    "postgresql+psycopg"
                    if self.DATABASE_TYPE == "postgres"
                    else "mysql+pymysql"
                ),
                username=self.DATABASE_USER,
                password=self.DATABASE_PASSWORD,
                host=self.DATABASE_SERVER,
                port=self.DATABASE_PORT,
                path=self.DATABASE_DB,
            )
        )

    ## BEHAVIOR

    LOGLEVEL: Literal["CRITICAL", "FATAL", "ERROR", "WARNING", "INFO", "DEBUG"] = "INFO"

    @computed_field
    @property
    def logging_loglevel(self) -> int:
        return getLevelNamesMapping().get(self.LOGLEVEL, INFO)

    # NOTIFICATIONS

    NOTIFY_PRIVATE_KEY: str
    NOTIFY_PUBLIC_KEY: str
    NOTIFY_BASE64_PUBKEY: str


settings = Settings()
