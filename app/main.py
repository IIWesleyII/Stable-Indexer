from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.indexer import router as indexer_router
from app.api.transfers import router as transfers_router
from app.api.metrics import router as metrics_router
from app.api.addresses import router as addresses_router
from app.database.base import Base
from app.database.session import engine
import app.database.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(
    title="Stable Indexer API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(indexer_router)
app.include_router(transfers_router)
app.include_router(metrics_router)
app.include_router(addresses_router)
