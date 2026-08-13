from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal

from app.database.session import get_session
from app.schemas.metrics import MetricsSummary
from app.services.metrics import get_summary_metrics
from app.schemas.metrics import TopAddress
from app.services.metrics import get_top_addresses
from app.schemas.metrics import DailyVolume
from app.services.metrics import get_daily_volume

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
)


@router.get(
    "/summary",
    response_model=MetricsSummary,
)
async def get_metrics_summary(
    chain: str | None = None,
    stablecoin: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> MetricsSummary:
    return await get_summary_metrics(
        session=session,
        chain=chain,
        stablecoin=stablecoin,
    )

@router.get(
    "/top-addresses",
    response_model=list[TopAddress],
)
async def top_addresses(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    sort_by: Literal[
        "transfer_count",
        "volume",
    ] = "transfer_count",
    chain: str | None = None,
    stablecoin: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[TopAddress]:
    return await get_top_addresses(
        session=session,
        limit=limit,
        chain=chain,
        stablecoin=stablecoin,
        sort_by=sort_by,
    )

@router.get(
    "/volume",
    response_model=list[DailyVolume],
)
async def daily_volume(
    days: int = Query(
        default=30,
        ge=1,
        le=365,
    ),
    chain: str | None = None,
    stablecoin: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[DailyVolume]:
    return await get_daily_volume(
        session=session,
        days=days,
        chain=chain,
        stablecoin=stablecoin,
    )