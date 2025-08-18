from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app.core.config import settings
from app.core.db import drop_db, engine, init_db
from app.api.main import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    with Session(engine) as session:
        init_db(session)

    yield

    if settings.LIFESPAN_DROP_DB:
        drop_db(engine)


logging.basicConfig(
    level=settings.logging_loglevel,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

logger.info("MEGAFON running!")

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

build_path = Path("frontend/build")
app.mount("/app", StaticFiles(directory=build_path), name="static")


@app.middleware("http")
async def fallback(request: Request, call_next):
    if request.url.path.startswith("/app"):
        relative_path = request.url.path.removeprefix("/app/").strip("/")
        target_file = build_path / relative_path

        if not target_file.exists() or target_file == build_path:
            return FileResponse(build_path / "index.html")

    return await call_next(request)


@app.get("/")
def index():
    return RedirectResponse("/app/")
