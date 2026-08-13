from decimal import Decimal

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import StablecoinTransfer
from app.database.session import get_session
from app.schemas.transfers import TransferRead


router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.get("", response_model=list[TransferRead])
async def get_transfers(
    chain: str | None = None,
    stablecoin: str | None = None,
    address: str | None = None,
    min_amount: Decimal | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> list[StablecoinTransfer]:
    statement = select(StablecoinTransfer)

    if chain:
        statement = statement.where(StablecoinTransfer.chain == chain)

    if stablecoin:
        statement = statement.where(
            StablecoinTransfer.token_symbol == stablecoin.upper()
        )

    if address:
        statement = statement.where(
            or_(
                StablecoinTransfer.from_address == address,
                StablecoinTransfer.to_address == address,
            )
        )

    if min_amount is not None:
        statement = statement.where(
            StablecoinTransfer.amount >= min_amount
        )

    statement = statement.order_by(
        StablecoinTransfer.block_number.desc(),
        StablecoinTransfer.log_index.desc(),
    ).limit(limit)

    result = await session.scalars(statement)
    return list(result)
