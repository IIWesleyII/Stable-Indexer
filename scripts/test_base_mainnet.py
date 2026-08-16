import asyncio

from app.blockchain.base import BaseIndexer


async def main() -> None:
    indexer = BaseIndexer()

    latest_block = await indexer.get_latest_block()

    print(f"Chain: {indexer.chain}")
    print(f"Latest block: {latest_block}")

    from_block = latest_block - 100
    to_block = latest_block

    print(
        f"Scanning blocks {from_block} to {to_block}..."
    )

    transfers = await indexer.get_transfers(
        from_block=from_block,
        to_block=to_block,
    )

    print(f"Found {len(transfers)} USDC transfers.")

    if not transfers:
        return

    print()
    print("Sample transfer:")
    print(transfers[0])


if __name__ == "__main__":
    asyncio.run(main())