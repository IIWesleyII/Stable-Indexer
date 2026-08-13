from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.blockchain.base_sepolia import BaseSepoliaIndexer
from app.database.session import get_session
from app.indexer.service import CheckpointNotInitializedError
from app.indexer.service import IndexerService
from app.schemas.transfers import CheckpointRead
from app.schemas.transfers import LatestBlockRead
from app.schemas.transfers import ScanRequest
from app.schemas.transfers import ScanResult
from app.schemas.transfers import SyncRequest
from app.schemas.transfers import SyncResult


router = APIRouter(prefix="/indexer", tags=["indexer"])


@router.get("/latest-block", response_model=LatestBlockRead)
async def get_latest_block() -> LatestBlockRead:
    indexer = BaseSepoliaIndexer()
    block_number = await indexer.get_latest_block()
    return LatestBlockRead(
        chain=indexer.chain,
        block_number=block_number,
    )


@router.get("/checkpoint", response_model=CheckpointRead)
async def get_checkpoint(
    session: AsyncSession = Depends(get_session),
) -> CheckpointRead:
    service = IndexerService(session)
    checkpoint = await service.get_checkpoint()

    if checkpoint is None:
        raise HTTPException(
            status_code=404,
            detail="No checkpoint exists yet. Run the first sync.",
        )

    return CheckpointRead.model_validate(checkpoint)


@router.post("/scan", response_model=ScanResult)
async def scan_blocks(
    request: ScanRequest,
    session: AsyncSession = Depends(get_session),
) -> ScanResult:
    service = IndexerService(session)
    return await service.scan(
        from_block=request.from_block,
        to_block=request.to_block,
    )


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
