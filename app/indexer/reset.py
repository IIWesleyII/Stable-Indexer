import argparse
import asyncio
import logging
from collections.abc import Sequence

from sqlalchemy import delete

from app.database.models import IndexerCheckpoint
from app.database.models import AddressMetric
from app.database.models import AddressTokenMetric
from app.database.models import ChainTokenMetric
from app.database.models import DailyStablecoinMetric
from app.database.models import StablecoinTransfer
from app.database.session import SessionLocal
from app.indexer.locks import IndexerLockedError
from app.indexer.locks import chain_lock
from app.indexer.worker import create_event_loop
from app.indexer.worker import get_worker_config


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete indexed data and the checkpoint for one chain.",
    )
    parser.add_argument(
        "--chain",
        required=True,
        help="Enabled chain to reset, such as base or ethereum.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required acknowledgement that this deletes chain data.",
    )

    args = parser.parse_args(argv)

    if not args.confirm:
        parser.error("--confirm is required to delete indexed data")

    return args


async def reset_chain(chain: str) -> tuple[int, bool]:
    config = get_worker_config(chain)

    async with chain_lock(config.chain):
        async with SessionLocal() as session:
            for model in (
                DailyStablecoinMetric,
                ChainTokenMetric,
                AddressMetric,
                AddressTokenMetric,
            ):
                await session.execute(
                    delete(model).where(
                        model.chain == config.chain
                    )
                )

            transfer_result = await session.execute(
                delete(StablecoinTransfer).where(
                    StablecoinTransfer.chain == config.chain
                )
            )
            checkpoint_result = await session.execute(
                delete(IndexerCheckpoint).where(
                    IndexerCheckpoint.chain == config.chain
                )
            )
            await session.commit()

    return (
        transfer_result.rowcount or 0,
        bool(checkpoint_result.rowcount),
    )


def main() -> None:
    args = parse_args()

    try:
        transfer_count, checkpoint_deleted = asyncio.run(
            reset_chain(args.chain),
            loop_factory=create_event_loop,
        )
    except IndexerLockedError:
        logger.error(
            "%s | reset blocked; stop the chain's importer or worker first",
            args.chain,
        )
        return
    except KeyboardInterrupt:
        logger.info("Chain reset cancelled")
        return

    logger.info(
        "%s | deleted %s transfers | checkpoint_deleted=%s",
        args.chain,
        transfer_count,
        checkpoint_deleted,
    )


if __name__ == "__main__":
    main()
