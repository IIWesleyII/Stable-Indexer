from typing import Protocol

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.blockchain.base_sepolia import BaseSepoliaIndexer
from app.database.models import IndexerCheckpoint
from app.database.models import StablecoinTransfer
from app.indexer.types import IndexedTransfer
from app.schemas.indexer import IndexerStatus
from app.schemas.transfers import ScanResult
from app.schemas.transfers import SyncResult


DB_INSERT_BATCH_SIZE = 1000


class CheckpointNotInitializedError(Exception):
    pass


class TransferIndexer(Protocol):
    chain: str

    async def get_latest_block(self) -> int:
        ...

    async def get_block_hash(self, block_number: int) -> str:
        ...

    async def get_transfers(
        self,
        from_block: int,
        to_block: int,
    ) -> list[IndexedTransfer]:
        ...


class IndexerService:
    def __init__(
        self,
        session: AsyncSession,
        indexer: TransferIndexer | None = None,
        batch_size: int = 500,
    ) -> None:
        self.session = session
        self.indexer = indexer or BaseSepoliaIndexer()
        self.batch_size = batch_size

    async def get_checkpoint(self) -> IndexerCheckpoint | None:
        return await self.session.get(
            IndexerCheckpoint,
            self.indexer.chain,
        )

    async def scan(
        self,
        from_block: int,
        to_block: int,
    ) -> ScanResult:
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
                "event_type": transfer.event_type,
            }
            for transfer in transfers
        ]

        inserted = 0

        try:
            for start in range(0, len(rows), DB_INSERT_BATCH_SIZE):
                batch = rows[
                    start:start + DB_INSERT_BATCH_SIZE
                ]

                statement = insert(
                    StablecoinTransfer
                ).values(batch)

                statement = statement.on_conflict_do_nothing(
                    constraint="uq_transfer_chain_tx_log"
                )

                statement = statement.returning(
                    StablecoinTransfer.id
                )

                result = await self.session.execute(statement)

                inserted += len(
                    result.scalars().all()
                )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return ScanResult(
            from_block=from_block,
            to_block=to_block,
            discovered=len(transfers),
            inserted=inserted,
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

            result = await self.scan(
                batch_start,
                batch_end,
            )

            total_discovered += result.discovered
            total_inserted += result.inserted
            batches += 1

            block_hash = await self.indexer.get_block_hash(
                batch_end
            )

            await self._save_checkpoint(
                batch_end,
                block_hash,
            )

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

    async def reposition_checkpoint(
        self,
        blocks_behind: int,
    ) -> dict:
        latest_block = await self.indexer.get_latest_block()

        next_block = latest_block - blocks_behind

        if next_block <= 0:
            raise ValueError(
                "blocks_behind is larger than the chain history"
            )

        checkpoint_block = next_block - 1

        block_hash = await self.indexer.get_block_hash(
            checkpoint_block
        )

        checkpoint = await self.get_checkpoint()

        if checkpoint is None:
            checkpoint = IndexerCheckpoint(
                chain=self.indexer.chain,
                last_processed_block=checkpoint_block,
                last_block_hash=block_hash,
            )

            self.session.add(checkpoint)
        else:
            checkpoint.last_processed_block = checkpoint_block
            checkpoint.last_block_hash = block_hash

        await self.session.commit()

        return {
            "chain": self.indexer.chain,
            "latest_block": latest_block,
            "last_processed_block": checkpoint_block,
            "next_block": next_block,
            "blocks_behind": blocks_behind,
        }

    async def get_status(self) -> IndexerStatus:
        latest_block = await self.indexer.get_latest_block()
        checkpoint = await self.get_checkpoint()

        if checkpoint is None:
            return IndexerStatus(
                chain=self.indexer.chain,
                latest_block=latest_block,
                last_processed_block=None,
                blocks_behind=None,
                caught_up=False,
                updated_at=None,
            )

        blocks_behind = max(
            latest_block - checkpoint.last_processed_block,
            0,
        )

        return IndexerStatus(
            chain=self.indexer.chain,
            latest_block=latest_block,
            last_processed_block=checkpoint.last_processed_block,
            blocks_behind=blocks_behind,
            caught_up=blocks_behind == 0,
            updated_at=checkpoint.updated_at,
        )