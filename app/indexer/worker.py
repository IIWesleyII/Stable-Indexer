import asyncio
import logging
import selectors

from app.database.session import SessionLocal
from app.indexer.service import CheckpointNotInitializedError
from app.indexer.service import IndexerService


MAX_BLOCKS_PER_SYNC = 500
POLL_INTERVAL_SECONDS = 5
CATCH_UP_DELAY_SECONDS = 1
ERROR_RETRY_SECONDS = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


async def sync_once():
    async with SessionLocal() as session:
        service = IndexerService(session)

        return await service.sync(
            start_block=None,
            max_blocks=MAX_BLOCKS_PER_SYNC,
        )


async def run_worker() -> None:
    logger.info("Starting Stable Indexer worker")

    while True:
        try:
            result = await sync_once()

        except CheckpointNotInitializedError as exc:
            logger.error("%s", exc)
            logger.error(
                "Run POST /indexer/sync once with a start_block."
            )
            return

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception("Indexer sync failed")
            await asyncio.sleep(ERROR_RETRY_SECONDS)
            continue

        if result.from_block is None:
            logger.info(
                "Caught up at block %s",
                result.latest_block,
            )
        else:
            logger.info(
                "Synced blocks %s-%s | discovered=%s | inserted=%s",
                result.from_block,
                result.to_block,
                result.discovered,
                result.inserted,
            )

        if result.caught_up:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
        else:
            await asyncio.sleep(CATCH_UP_DELAY_SECONDS)


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
        logger.info("Stable Indexer worker stopped")


if __name__ == "__main__":
    main()