import argparse
import asyncio
import logging
from collections.abc import Sequence

from app.blockchain.chains import BASE_MAINNET
from app.blockchain.chains import ETHEREUM_MAINNET
from app.blockchain.evm import EvmIndexer
from app.blockchain.tokens import BASE_USDC
from app.blockchain.tokens import ETHEREUM_USDC
from app.database.session import SessionLocal
from app.indexer.alchemy import AlchemyTransferClient
from app.indexer.locks import chain_lock
from app.indexer.service import IndexerService
from app.indexer.worker import create_event_loop


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import historical USDC transfers from Alchemy.",
    )
    parser.add_argument(
        "--chain",
        required=True,
        choices=("base", "ethereum"),
        help="EVM chain to import.",
    )
    parser.add_argument(
        "--start-block",
        required=True,
        type=int,
        help="First block to import, inclusive.",
    )
    parser.add_argument(
        "--end-block",
        type=int,
        help="Last block to import, inclusive. Defaults to the current head.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="Import only this many pages without advancing the checkpoint.",
    )

    args = parser.parse_args(argv)

    if args.start_block < 0:
        parser.error("--start-block must not be negative")

    if args.end_block is not None and args.end_block < args.start_block:
        parser.error("--end-block must not be before --start-block")

    if args.max_pages is not None and args.max_pages < 1:
        parser.error("--max-pages must be at least 1")

    return args


def get_import_config(
    chain: str,
) -> tuple[EvmIndexer, AlchemyTransferClient]:
    if chain == "base":
        indexer = EvmIndexer(BASE_MAINNET, BASE_USDC)
    elif chain == "ethereum":
        if not ETHEREUM_MAINNET.rpc_url:
            raise ValueError("ETHEREUM_RPC_URL is required")
        indexer = EvmIndexer(ETHEREUM_MAINNET, ETHEREUM_USDC)
    else:
        raise ValueError(f"Unsupported historical import chain: {chain}")

    client = AlchemyTransferClient(
        chain=indexer.chain,
        rpc_url=indexer.chain_config.rpc_url,
        token=indexer.token,
    )

    return indexer, client


async def run_import(
    chain: str,
    start_block: int,
    end_block: int | None,
    max_pages: int | None,
) -> None:
    indexer, client = get_import_config(chain)

    try:
        async with chain_lock(indexer.chain, wait=True):
            final_block = end_block
            if final_block is None:
                final_block = await indexer.get_latest_block()

            logger.info(
                "%s | importing Alchemy USDC transfers from blocks %s-%s",
                indexer.chain,
                start_block,
                final_block,
            )

            discovered = 0
            inserted = 0
            page_count = 0

            async with SessionLocal() as session:
                service = IndexerService(session=session, indexer=indexer)

                async for transfers in client.iter_transfers(
                    from_block=start_block,
                    to_block=final_block,
                    max_pages=max_pages,
                ):
                    result = await service.insert_transfers(transfers)
                    discovered += result["discovered"]
                    inserted += result["inserted"]
                    page_count += 1

                    logger.info(
                        "%s | imported page %s | discovered=%s | "
                        "inserted=%s",
                        indexer.chain,
                        page_count,
                        result["discovered"],
                        result["inserted"],
                    )

                if max_pages is not None:
                    logger.info(
                        "%s | test import stopped after %s pages; "
                        "checkpoint unchanged",
                        indexer.chain,
                        page_count,
                    )
                    return

                block_hash = await indexer.get_block_hash(final_block)
                await service.save_checkpoint(final_block, block_hash)

            logger.info(
                "%s | historical import complete | pages=%s | "
                "discovered=%s | inserted=%s | checkpoint=%s",
                indexer.chain,
                page_count,
                discovered,
                inserted,
                final_block,
            )
    finally:
        await client.close()
        await indexer.close()


def main() -> None:
    args = parse_args()

    try:
        asyncio.run(
            run_import(
                chain=args.chain,
                start_block=args.start_block,
                end_block=args.end_block,
                max_pages=args.max_pages,
            ),
            loop_factory=create_event_loop,
        )
    except KeyboardInterrupt:
        logger.info("Historical import interrupted")


if __name__ == "__main__":
    main()
