from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.health import router as health_router
from app.api.indexer import router as indexer_router
from app.api.transfers import router as transfers_router
from app.api.metrics import router as metrics_router
from app.api.addresses import router as addresses_router
from app.database.base import Base
from app.database.session import engine
from app.api.watchlists import router as watchlists_router

import app.database.models  # noqa: F401


async def create_transfer_lookup_indexes() -> None:
    statements = (
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
        "ix_transfer_chain_token_event_from_lower "
        "ON stablecoin_transfers "
        "(chain, token_symbol, event_type, lower(from_address))",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
        "ix_transfer_chain_token_event_to_lower "
        "ON stablecoin_transfers "
        "(chain, token_symbol, event_type, lower(to_address))",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
        "ix_transfer_chain_token_event_from_exact "
        "ON stablecoin_transfers "
        "(chain, token_symbol, event_type, from_address)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
        "ix_transfer_chain_token_event_to_exact "
        "ON stablecoin_transfers "
        "(chain, token_symbol, event_type, to_address)",
    )

    async with engine.connect() as connection:
        autocommit_connection = await connection.execution_options(
            isolation_level="AUTOCOMMIT",
        )

        for statement in statements:
            await autocommit_connection.execute(text(statement))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(
            text(
                "ALTER TABLE stablecoin_transfers "
                "ALTER COLUMN transaction_hash TYPE VARCHAR(128)"
            )
        )

    await create_transfer_lookup_indexes()

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
app.include_router(watchlists_router)
