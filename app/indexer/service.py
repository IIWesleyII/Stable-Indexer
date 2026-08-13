from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.blockchain.base_sepolia import BaseSepoliaIndexer
from app.database.models import IndexerCheckpoint
from app.database.models import StablecoinTransfer
from app.schemas.transfers import ScanResult
from app.schemas.transfers import SyncResult


class CheckpointNotInitializedError(Exception):
    pass


class IndexerService:
    batch_size = 500

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.indexer = BaseSepoliaIndexer()

    async def get_checkpoint(self) -> IndexerCheckpoint | None:
        return await self.session.get(
            IndexerCheckpoint,
            self.indexer.chain,
        )

    async def scan(self, from_block: int, to_block: int) -> ScanResult:
        transfers = await self.indexer.get_transfers(
            from_block=from_block,
            to_block=to_block,
        )

        if not transfers:
            return ScanResult(
                from_block=from_block,
                to_block=to_block,
                discovered=0,
                inserted=0,
            )

        rows = [
            {
                "chain": transfer.chain,
                "token_symbol": transfer.token_symbol,
                "token_address": transfer.token_address,
                "transaction_hash": transfer.transaction_hash,
                "log_index": transfer.log_index,
                "block_number": transfer.block_number,
                "block_hash": transfer.block_hash,
                "timestamp": transfer.timestamp,
                "from_address": transfer.from_address,
                "to_address": transfer.to_address,
                "amount_raw": transfer.amount_raw,
                "amount": transfer.amount,
            }
            for transfer in transfers
        ]

        statement = insert(StablecoinTransfer).values(rows)
        statement = statement.on_conflict_do_nothing(
            constraint="uq_transfer_chain_tx_log"
        )
        statement = statement.returning(StablecoinTransfer.id)

        result = await self.session.execute(statement)
        inserted_ids = result.scalars().all()
        await self.session.commit()

        return ScanResult(
            from_block=from_block,
            to_block=to_block,
            discovered=len(transfers),
            inserted=len(inserted_ids),
        )

    async def sync(
        self,
        start_block: int | None,
        max_blocks: int,
    ) -> SyncResult:
        latest_block = await self.indexer.get_latest_block()
        checkpoint = await self.get_checkpoint()

        if checkpoint is None:
            if start_block is None:
                raise CheckpointNotInitializedError(
                    "start_block is required for the first sync"
                )
            next_block = start_block
        else:
            next_block = checkpoint.last_processed_block + 1

        if next_block > latest_block:
            return SyncResult(
                chain=self.indexer.chain,
                from_block=None,
                to_block=None,
                latest_block=latest_block,
                discovered=0,
                inserted=0,
                batches=0,
                caught_up=True,
            )

        sync_to = min(
            latest_block,
            next_block + max_blocks - 1,
        )
        total_discovered = 0
        total_inserted = 0
        batches = 0
        batch_start = next_block

        while batch_start <= sync_to:
            batch_end = min(
                batch_start + self.batch_size - 1,
                sync_to,
            )
            result = await self.scan(batch_start, batch_end)
            total_discovered += result.discovered
            total_inserted += result.inserted
            batches += 1

            block_hash = await self.indexer.get_block_hash(batch_end)
            await self._save_checkpoint(batch_end, block_hash)
            batch_start = batch_end + 1

        return SyncResult(
            chain=self.indexer.chain,
            from_block=next_block,
            to_block=sync_to,
            latest_block=latest_block,
            discovered=total_discovered,
            inserted=total_inserted,
            batches=batches,
            caught_up=sync_to == latest_block,
        )

    async def _save_checkpoint(
        self,
        block_number: int,
        block_hash: str,
    ) -> None:
        checkpoint = await self.get_checkpoint()

        if checkpoint is None:
            checkpoint = IndexerCheckpoint(
                chain=self.indexer.chain,
                last_processed_block=block_number,
                last_block_hash=block_hash,
            )
            self.session.add(checkpoint)
        else:
            checkpoint.last_processed_block = block_number
            checkpoint.last_block_hash = block_hash

        await self.session.commit()
