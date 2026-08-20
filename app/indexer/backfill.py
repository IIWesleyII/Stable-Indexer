import argparse
import asyncio
import logging
from collections.abc import Sequence

from app.database.session import SessionLocal
from app.indexer.locks import chain_lock
from app.indexer.service import IndexerService
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
        description="Backfill stablecoin transfers for one chain.",
    )
    parser.add_argument(
        "--chain",
        required=True,
        help="Enabled chain to backfill, such as base or ethereum.",
    )
    parser.add_argument(
        "--start-block",
        type=int,
        help="First block or Solana slot to index.",
    )
    parser.add_argument(
        "--previous-hours",
        type=int,
        help=(
            "Rewind to this many hours before the current EVM head. "
            "Requires --rewind."
        ),
    )
    parser.add_argument(
        "--rewind",
        action="store_true",
        help="Move an existing checkpoint back to --start-block.",
    )
    parser.add_argument(
        "--max-syncs",
        type=int,
        help="Stop after this many sync cycles instead of catching up.",
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=0.2,
        help="Delay between catch-up sync cycles. Defaults to 0.2.",
    )

    args = parser.parse_args(argv)

    if args.start_block is not None and args.start_block < 0:
        parser.error("--start-block must not be negative")

    if (
        args.start_block is not None
        and args.previous_hours is not None
    ):
        parser.error(
            "Use either --start-block or --previous-hours"
        )

    if args.previous_hours is not None and args.previous_hours < 1:
        parser.error("--previous-hours must be at least 1")

    if (
        args.rewind
        and args.start_block is None
        and args.previous_hours is None
    ):
        parser.error(
            "--rewind requires --start-block or --previous-hours"
        )

    if args.previous_hours is not None and not args.rewind:
        parser.error("--previous-hours requires --rewind")

    if args.max_syncs is not None and args.max_syncs < 1:
        parser.error("--max-syncs must be at least 1")

    if args.delay_seconds < 0:
        parser.error("--delay-seconds must not be negative")

    return args


async def run_backfill(
    chain: str,
    start_block: int | None,
    previous_hours: int | None,
    rewind: bool,
    max_syncs: int | None,
    delay_seconds: float,
) -> None:
    config = get_worker_config(chain)
    indexer = config.indexer_factory()

    try:
        logger.info(
            "%s | waiting for the chain lock",
            indexer.chain,
        )

        async with chain_lock(indexer.chain, wait=True):
            if previous_hours is not None:
                if config.initial_lookback_seconds is None:
                    raise ValueError(
                        "--previous-hours is supported only for EVM chains"
                    )

                latest_block = await indexer.get_latest_block()
                latest_timestamp = await indexer.get_block_timestamp(
                    latest_block
                )
                target_timestamp = latest_timestamp - (
                    previous_hours * 60 * 60
                )
                start_block = (
                    await indexer.get_block_at_or_after_timestamp(
                        target_timestamp,
                        latest_block,
                    )
                )

                logger.info(
                    "%s | resolved previous %s hours to block %s",
                    indexer.chain,
                    previous_hours,
                    start_block,
                )

            async with SessionLocal() as session:
                service = IndexerService(
                    session=session,
                    indexer=indexer,
                    batch_size=config.batch_size,
                )
                checkpoint = await service.get_checkpoint()

                if checkpoint is None:
                    if start_block is None:
                        raise ValueError(
                            "--start-block is required when the chain "
                            "has no checkpoint"
                        )

                    await service.rewind_checkpoint(start_block)
                    logger.info(
                        "%s | initialized backfill at block %s",
                        indexer.chain,
                        start_block,
                    )
                elif rewind:
                    await service.rewind_checkpoint(start_block)
                    logger.info(
                        "%s | rewound backfill to block %s",
                        indexer.chain,
                        start_block,
                    )
                elif start_block is not None:
                    raise ValueError(
                        "A checkpoint already exists. Use --rewind to "
                        "move it back, or omit --start-block to resume."
                    )

                sync_count = 0

                while max_syncs is None or sync_count < max_syncs:
                    result = await service.sync(
                        start_block=None,
                        max_blocks=config.max_blocks_per_sync,
                    )
                    sync_count += 1

                    if result.from_block is None:
                        logger.info(
                            "%s | backfill caught up at block %s",
                            indexer.chain,
                            result.latest_block,
                        )
                        return

                    logger.info(
                        "%s | backfilled blocks %s-%s | "
                        "discovered=%s | inserted=%s",
                        indexer.chain,
                        result.from_block,
                        result.to_block,
                        result.discovered,
                        result.inserted,
                    )

                    if result.caught_up:
                        logger.info(
                            "%s | backfill caught up at block %s",
                            indexer.chain,
                            result.latest_block,
                        )
                        return

                    if delay_seconds:
                        await asyncio.sleep(delay_seconds)

                logger.info(
                    "%s | stopped after %s sync cycles; rerun without "
                    "--max-syncs to resume",
                    indexer.chain,
                    sync_count,
                )
    finally:
        await indexer.close()


def main() -> None:
    args = parse_args()

    try:
        asyncio.run(
            run_backfill(
                chain=args.chain,
                start_block=args.start_block,
                previous_hours=args.previous_hours,
                rewind=args.rewind,
                max_syncs=args.max_syncs,
                delay_seconds=args.delay_seconds,
            ),
            loop_factory=create_event_loop,
        )
    except KeyboardInterrupt:
        logger.info("Backfill interrupted; rerun the command to resume")


if __name__ == "__main__":
    main()
