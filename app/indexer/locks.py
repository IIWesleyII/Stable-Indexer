import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text

from app.database.session import engine


class IndexerLockedError(Exception):
    pass


@asynccontextmanager
async def chain_lock(
    chain: str,
    wait: bool = False,
) -> AsyncIterator[None]:
    async with engine.connect() as connection:
        while True:
            result = await connection.execute(
                text(
                    "SELECT pg_try_advisory_lock("
                    "hashtextextended(:chain, 0)"
                    ")"
                ),
                {"chain": chain},
            )

            if result.scalar_one():
                break

            if not wait:
                raise IndexerLockedError(
                    f"{chain} is locked by another indexer run"
                )

            await asyncio.sleep(1)

        try:
            yield
        finally:
            await connection.execute(
                text(
                    "SELECT pg_advisory_unlock("
                    "hashtextextended(:chain, 0)"
                    ")"
                ),
                {"chain": chain},
            )
