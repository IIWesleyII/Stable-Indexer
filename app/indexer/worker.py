import asyncio
import logging
import selectors
from dataclasses import dataclass
from typing import Callable

from app.blockchain.base import BaseIndexer
from app.blockchain.base_sepolia import BaseSepoliaIndexer
from app.database.session import SessionLocal
from app.indexer.service import CheckpointNotInitializedError
from app.indexer.service import IndexerService
from app.indexer.service import TransferIndexer


POLL_INTERVAL_SECONDS = 5
CATCH_UP_DELAY_SECONDS = 1
ERROR_RETRY_SECONDS = 10


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkerConfig:
    indexer_factory: Callable[[], TransferIndexer]
    batch_size: int
    max_blocks_per_sync: int
    initial_blocks_behind: int | None = None


WORKERS = (
    WorkerConfig(
        indexer_factory=BaseSepoliaIndexer,
        batch_size=500,
        max_blocks_per_sync=500,
    ),
    WorkerConfig(
        indexer_factory=BaseIndexer,
        batch_size=25,
        max_blocks_per_sync=100,
        initial_blocks_behind=1000,
    ),
)


async def sync_once(
    config: WorkerConfig,
):
    indexer = config.indexer_factory()

    async with SessionLocal() as session:
        service = IndexerService(
            session=session,
            indexer=indexer,
            batch_size=config.batch_size,
        )

        checkpoint = await service.get_checkpoint()
        start_block = None

        if (
            checkpoint is None
            and config.initial_blocks_behind is not None
        ):
            latest_block = await indexer.get_latest_block()

            start_block = max(
                latest_block - config.initial_blocks_behind,
                0,
            )

            logger.info(
                "%s | initializing %s blocks behind at block %s",
                indexer.chain,
                config.initial_blocks_behind,
                start_block,
            )

        return await service.sync(
            start_block=start_block,
            max_blocks=config.max_blocks_per_sync,
        )


async def run_chain_worker(
    config: WorkerConfig,
) -> None:
    chain = config.indexer_factory().chain

    logger.info(
        "%s | worker started",
        chain,
    )

    while True:
        try:
            result = await sync_once(config)

        except CheckpointNotInitializedError as exc:
            logger.error(
                "%s | %s",
                chain,
                exc,
            )

            logger.error(
                "%s | initialize the checkpoint before starting",
                chain,
            )

            return

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception(
                "%s | indexer sync failed",
                chain,
            )

            await asyncio.sleep(
                ERROR_RETRY_SECONDS
            )

            continue

        if result.from_block is None:
            logger.info(
                "%s | caught up at block %s",
                chain,
                result.latest_block,
            )
        else:
            logger.info(
                "%s | synced blocks %s-%s | "
                "discovered=%s | inserted=%s",
                chain,
                result.from_block,
                result.to_block,
                result.discovered,
                result.inserted,
            )

        if result.caught_up:
            await asyncio.sleep(
                POLL_INTERVAL_SECONDS
            )
        else:
            await asyncio.sleep(
                CATCH_UP_DELAY_SECONDS
            )


async def run_worker() -> None:
    logger.info("Starting Stable Indexer workers")

    await asyncio.gather(
        *(
            run_chain_worker(config)
            for config in WORKERS
        )
    )


def create_event_loop() -> asyncio.AbstractEventLoop:
    selector = selectors.SelectSelector()

    return asyncio.SelectorEventLoop(selector)


def main() -> None:
    try:
        asyncio.run(
            run_worker(),
            loop_factory=create_event_loop,
        )
    except KeyboardInterrupt:
        logger.info("Stable Indexer workers stopped")


if __name__ == "__main__":
    main()