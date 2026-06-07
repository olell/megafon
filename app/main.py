import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete
from sqlmodel import Session

from app.core.config import settings
from app.core.db import drop_db, engine, init_db
from app.models.models import Event
from app.api.main import router as api_router
from app.api.metrics import router as metrics_router

# Feed events older than this are pruned; only recent ones are ever replayed.
EVENT_RETENTION_HOURS = 24


async def _prune_events():
    """Periodically drop stale rows from the SSE event log so it can't grow
    unbounded. Runs in every worker; the DELETE is idempotent."""
    while True:
        await asyncio.sleep(3600)
        try:
            with Session(engine) as session:
                cutoff = datetime.now() - timedelta(hours=EVENT_RETENTION_HOURS)
                session.execute(delete(Event).where(Event.created_at < cutoff))
                session.commit()
        except Exception:
            logger.exception("Event log prune failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    with Session(engine) as session:
        init_db(session)

    prune_task = asyncio.create_task(_prune_events())

    yield

    prune_task.cancel()

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
# Prometheus scrape target at the conventional root path /metrics.
app.include_router(metrics_router)

build_path = Path("frontend/build")
build_path.mkdir(parents=True, exist_ok=True)
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
