from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.blockchain.base import BaseIndexer
from app.blockchain.ethereum import EthereumIndexer
from app.blockchain.solana import SolanaIndexer
from app.blockchain.tron import TronIndexer
from app.config import settings
from app.database.session import get_session
from app.indexer.service import CheckpointNotInitializedError
from app.indexer.service import IndexerService
from app.schemas.transfers import CheckpointRead
from app.schemas.transfers import LatestBlockRead
from app.schemas.transfers import ScanRequest
from app.schemas.transfers import ScanResult
from app.schemas.transfers import SyncRequest
from app.schemas.transfers import SyncResult
from app.schemas.indexer import IndexerStatus

from pydantic import BaseModel
from pydantic import Field
class RepositionCheckpointRequest(BaseModel):
    blocks_behind: int = Field(
        default=50000,
        ge=1000,
        le=500000,
    )

router = APIRouter(prefix="/indexer", tags=["indexer"])


@router.get("/latest-block", response_model=LatestBlockRead)
async def get_latest_block() -> LatestBlockRead:
    indexer = BaseIndexer()

    try:
        block_number = await indexer.get_latest_block()
        return LatestBlockRead(
            chain=indexer.chain,
            block_number=block_number,
        )
    finally:
        await indexer.close()


@router.get("/checkpoint", response_model=CheckpointRead)
async def get_checkpoint(
    session: AsyncSession = Depends(get_session),
) -> CheckpointRead:
    service = IndexerService(session)

    try:
        checkpoint = await service.get_checkpoint()

        if checkpoint is None:
            raise HTTPException(
                status_code=404,
                detail="No checkpoint exists yet. Run the first sync.",
            )

        return CheckpointRead.model_validate(checkpoint)
    finally:
        await service.indexer.close()


@router.post("/scan", response_model=ScanResult)
async def scan_blocks(
    request: ScanRequest,
    session: AsyncSession = Depends(get_session),
) -> ScanResult:
    service = IndexerService(session)

    try:
        return await service.scan(
            from_block=request.from_block,
            to_block=request.to_block,
        )
    finally:
        await service.indexer.close()


@router.post("/sync", response_model=SyncResult)
async def sync_blocks(
    request: SyncRequest,
    session: AsyncSession = Depends(get_session),
) -> SyncResult:
    service = IndexerService(session)

    try:
        return await service.sync(
            start_block=request.start_block,
            max_blocks=request.max_blocks,
        )
    except CheckpointNotInitializedError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    finally:
        await service.indexer.close()

@router.post("/checkpoint/reposition")
async def reposition_checkpoint(
    request: RepositionCheckpointRequest,
    session: AsyncSession = Depends(get_session),
):
    service = IndexerService(session)

    try:
        return await service.reposition_checkpoint(
            blocks_behind=request.blocks_behind,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    finally:
        await service.indexer.close()


@router.get(
    "/status",
    response_model=list[IndexerStatus],
)
async def indexer_status(
    session: AsyncSession = Depends(get_session),
) -> list[IndexerStatus]:
    statuses = []

    indexers = [BaseIndexer()]

    if settings.ethereum_rpc_url:
        indexers.insert(
            1,
            EthereumIndexer(),
        )

    if settings.solana_rpc_url:
        indexers.append(SolanaIndexer())

    if settings.trongrid_api_key:
        indexers.append(TronIndexer())

    try:
        for indexer in indexers:
            service = IndexerService(
                session=session,
                indexer=indexer,
            )

            statuses.append(
                await service.get_status()
            )

        return statuses
    finally:
        for indexer in indexers:
            await indexer.close()
