import argparse
import asyncio
import logging
from collections.abc import Sequence
from contextlib import AsyncExitStack

from sqlalchemy import delete
from sqlalchemy import text

from app.database.base import Base
from app.database.models import AddressMetric
from app.database.models import AddressTokenMetric
from app.database.models import ChainTokenMetric
from app.database.models import DailyStablecoinMetric
from app.database.session import SessionLocal
from app.database.session import engine
from app.indexer.locks import chain_lock
from app.indexer.worker import create_event_loop
from app.indexer.worker import get_worker_config
from app.indexer.worker import get_worker_configs


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild dashboard metric rollups from raw transfers.",
    )
    parser.add_argument(
        "--chain",
        help="Rebuild one enabled chain. Defaults to every enabled chain.",
    )
    return parser.parse_args(argv)


async def rebuild_metrics(chain: str | None = None) -> None:
    configs = (
        (get_worker_config(chain),)
        if chain is not None
        else get_worker_configs()
    )
    chains = [config.chain for config in configs]

    async with AsyncExitStack() as stack:
        for indexed_chain in chains:
            await stack.enter_async_context(
                chain_lock(indexed_chain, wait=True)
            )

        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        logger.info(
            "rebuilding dashboard rollups for %s",
            ", ".join(chains),
        )

        async with SessionLocal() as session:
            for model in (
                DailyStablecoinMetric,
                ChainTokenMetric,
                AddressMetric,
                AddressTokenMetric,
            ):
                statement = delete(model)
                if chain is not None:
                    statement = statement.where(model.chain == chain)
                await session.execute(statement)

            params = {"chain": chain} if chain is not None else {}
            filter_sql = "event_type = 'transfer'"
            if chain is not None:
                filter_sql += " AND chain = :chain"
            await session.execute(
                text(
                    "INSERT INTO daily_stablecoin_metrics ("
                    "chain, token_symbol, date, transfer_count, volume"
                    ") "
                    "SELECT chain, token_symbol, timestamp::date, "
                    "COUNT(*), SUM(amount) "
                    "FROM stablecoin_transfers "
                    f"WHERE {filter_sql} "
                    "GROUP BY chain, token_symbol, timestamp::date"
                ),
                params,
            )
            await session.execute(
                text(
                    "INSERT INTO chain_token_metrics ("
                    "chain, token_symbol, transfer_count, total_volume, "
                    "largest_transfer, smallest_transfer"
                    ") "
                    "SELECT chain, token_symbol, COUNT(*), SUM(amount), "
                    "MAX(amount), MIN(amount) "
                    "FROM stablecoin_transfers "
                    f"WHERE {filter_sql} "
                    "GROUP BY chain, token_symbol"
                ),
                params,
            )

            activity_cte = (
                "WITH activity AS ("
                "SELECT chain, token_symbol, "
                "CASE WHEN chain IN ('solana', 'tron') THEN from_address "
                "ELSE lower(from_address) END AS address, "
                "1 AS sent_count, 0 AS received_count, amount AS sent_volume, "
                "0::numeric AS received_volume "
                "FROM stablecoin_transfers "
                f"WHERE {filter_sql} "
                "UNION ALL "
                "SELECT chain, token_symbol, "
                "CASE WHEN chain IN ('solana', 'tron') THEN to_address "
                "ELSE lower(to_address) END AS address, "
                "0 AS sent_count, 1 AS received_count, 0::numeric AS sent_volume, "
                "amount AS received_volume "
                "FROM stablecoin_transfers "
                f"WHERE {filter_sql}"
                ") "
            )
            await session.execute(
                text(
                    activity_cte
                    + "INSERT INTO address_metrics ("
                    "chain, address, sent_count, received_count, activity_count, "
                    "sent_volume, received_volume, activity_volume"
                    ") "
                    "SELECT chain, address, SUM(sent_count), SUM(received_count), "
                    "SUM(sent_count + received_count), SUM(sent_volume), "
                    "SUM(received_volume), SUM(sent_volume + received_volume) "
                    "FROM activity GROUP BY chain, address"
                ),
                params,
            )
            await session.execute(
                text(
                    activity_cte
                    + "INSERT INTO address_token_metrics ("
                    "chain, address, token_symbol, sent_count, received_count, "
                    "activity_count, sent_volume, received_volume, activity_volume"
                    ") "
                    "SELECT chain, address, token_symbol, SUM(sent_count), "
                    "SUM(received_count), SUM(sent_count + received_count), "
                    "SUM(sent_volume), SUM(received_volume), "
                    "SUM(sent_volume + received_volume) "
                    "FROM activity GROUP BY chain, address, token_symbol"
                ),
                params,
            )
            await session.commit()

    logger.info("dashboard rollups rebuilt")


def main() -> None:
    args = parse_args()
    asyncio.run(
        rebuild_metrics(args.chain),
        loop_factory=create_event_loop,
    )


if __name__ == "__main__":
    main()
