from sqlalchemy import func
from sqlalchemy import literal
from sqlalchemy import select
from sqlalchemy import union
from sqlalchemy import union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import StablecoinTransfer
from app.schemas.metrics import DailyVolume
from app.schemas.metrics import MetricsSummary
from app.schemas.metrics import TopAddress

async def get_summary_metrics(
    session: AsyncSession,
    chain: str | None = None,
    stablecoin: str | None = "USDC",
) -> MetricsSummary:
    conditions = [
        StablecoinTransfer.event_type == "transfer",
    ]

    if chain is not None:
        conditions.append(
            StablecoinTransfer.chain == chain
        )

    if stablecoin is not None:
        conditions.append(
            StablecoinTransfer.token_symbol == stablecoin
        )

    summary_statement = select(
        func.count(StablecoinTransfer.id).label("transfer_count"),
        func.coalesce(
            func.sum(StablecoinTransfer.amount),
            0,
        ).label("total_volume"),
        func.coalesce(
            func.max(StablecoinTransfer.amount),
            0,
        ).label("largest_transfer"),
        func.coalesce(
            func.min(StablecoinTransfer.amount),
            0,
        ).label("smallest_transfer"),
    ).where(*conditions)

    summary_result = await session.execute(summary_statement)
    summary = summary_result.one()

    addresses_statement = union(
        select(
            StablecoinTransfer.chain.label("chain"),
            func.lower(
                StablecoinTransfer.from_address
            ).label("address"),
        ).where(*conditions),
        select(
            StablecoinTransfer.chain.label("chain"),
            func.lower(
                StablecoinTransfer.to_address
            ).label("address"),
        ).where(*conditions),
    ).subquery()

    unique_statement = select(
        func.count().label("unique_addresses")
    ).select_from(addresses_statement)

    unique_result = await session.execute(unique_statement)
    unique_addresses = unique_result.scalar_one()

    return MetricsSummary(
        transfer_count=summary.transfer_count,
        total_volume=summary.total_volume,
        largest_transfer=summary.largest_transfer,
        smallest_transfer=summary.smallest_transfer,
        unique_addresses=unique_addresses,
    )

async def get_top_addresses(
    session: AsyncSession,
    limit: int = 10,
    sort_by: str = "volume",
    chain: str | None = None,
    stablecoin: str | None = "USDC",
) -> list[TopAddress]:
    conditions = [
        StablecoinTransfer.event_type == "transfer",
    ]

    if chain is not None:
        conditions.append(
            StablecoinTransfer.chain == chain
        )

    if stablecoin is not None:
        conditions.append(
            StablecoinTransfer.token_symbol == stablecoin
        )

    sent = (
        select(
            StablecoinTransfer.chain.label("chain"),
            func.lower(
                StablecoinTransfer.from_address
            ).label("address"),
            literal(1).label("sent_count"),
            literal(0).label("received_count"),
            StablecoinTransfer.amount.label("sent_volume"),
            literal(0).label("received_volume"),
        )
        .where(*conditions)
    )

    received = (
        select(
            StablecoinTransfer.chain.label("chain"),
            func.lower(
                StablecoinTransfer.to_address
            ).label("address"),
            literal(0).label("sent_count"),
            literal(1).label("received_count"),
            literal(0).label("sent_volume"),
            StablecoinTransfer.amount.label("received_volume"),
        )
        .where(*conditions)
    )

    activity = union_all(
        sent,
        received,
    ).subquery()

    sent_count = func.sum(
        activity.c.sent_count
    ).label("sent_count")

    received_count = func.sum(
        activity.c.received_count
    ).label("received_count")

    transfer_count = (
        sent_count + received_count
    ).label("transfer_count")

    sent_volume = func.sum(
        activity.c.sent_volume
    ).label("sent_volume")

    received_volume = func.sum(
        activity.c.received_volume
    ).label("received_volume")

    activity_volume = (
        sent_volume + received_volume
    ).label("activity_volume")

    if sort_by == "volume":
        order_by = (
            activity_volume.desc(),
            transfer_count.desc(),
        )
    else:
        order_by = (
            transfer_count.desc(),
            activity_volume.desc(),
        )

    statement = (
        select(
            activity.c.chain,
            activity.c.address,
            transfer_count,
            sent_count,
            received_count,
            sent_volume,
            received_volume,
            activity_volume,
        )
        .group_by(
            activity.c.chain,
            activity.c.address,
        )
        .order_by(*order_by)
        .limit(limit)
    )

    result = await session.execute(statement)

    return [
        TopAddress(**row)
        for row in result.mappings().all()
    ]

async def get_daily_volume(
    session: AsyncSession,
    days: int = 30,
    chain: str | None = None,
    stablecoin: str | None = "USDC",
) -> list[DailyVolume]:
    conditions = [
        StablecoinTransfer.event_type == "transfer",
    ]

    if chain is not None:
        conditions.append(
            StablecoinTransfer.chain == chain
        )

    if stablecoin is not None:
        conditions.append(
            StablecoinTransfer.token_symbol == stablecoin
        )

    day = func.date(
        StablecoinTransfer.timestamp
    ).label("date")

    statement = (
        select(
            day,
            func.count(
                StablecoinTransfer.id
            ).label("transfer_count"),
            func.sum(
                StablecoinTransfer.amount
            ).label("volume"),
        )
        .where(*conditions)
        .group_by(day)
        .order_by(day.desc())
        .limit(days)
    )

    result = await session.execute(statement)
    rows = result.mappings().all()

    return [
        DailyVolume(**row)
        for row in reversed(rows)
    ]