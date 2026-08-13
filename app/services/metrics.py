from decimal import Decimal

from sqlalchemy import case
from sqlalchemy import Numeric
from sqlalchemy import distinct
from sqlalchemy import func
from sqlalchemy import literal
from sqlalchemy import select
from sqlalchemy import union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import StablecoinTransfer
from app.schemas.metrics import MetricsSummary
from app.schemas.metrics import TopAddress
from app.schemas.metrics import DailyVolume

async def get_summary_metrics(
    session: AsyncSession,
    chain: str | None = None,
    stablecoin: str | None = None,
) -> MetricsSummary:
    conditions = []

    if chain:
        conditions.append(
            StablecoinTransfer.chain == chain
        )

    if stablecoin:
        conditions.append(
            StablecoinTransfer.token_symbol == stablecoin.upper()
        )

    summary_statement = select(
        func.count(
            StablecoinTransfer.id
        ).label("transfer_count"),
        func.sum(
            StablecoinTransfer.amount
        ).label("total_volume"),
        func.max(
            StablecoinTransfer.amount
        ).label("largest_transfer"),
        func.min(
            case(
                (
                    StablecoinTransfer.amount > 0,
                    StablecoinTransfer.amount,
                )
            )
        ).label("smallest_transfer"),
    )

    if conditions:
        summary_statement = summary_statement.where(
            *conditions
        )

    summary_result = await session.execute(
        summary_statement
    )
    summary = summary_result.one()

    from_addresses = select(
        StablecoinTransfer.from_address.label("address")
    )

    to_addresses = select(
        StablecoinTransfer.to_address.label("address")
    )

    if conditions:
        from_addresses = from_addresses.where(
            *conditions
        )
        to_addresses = to_addresses.where(
            *conditions
        )

    addresses = union_all(
        from_addresses,
        to_addresses,
    ).subquery()

    address_statement = select(
        func.count(
            distinct(addresses.c.address)
        )
    )

    unique_addresses = await session.scalar(
        address_statement
    )

    return MetricsSummary(
        transfer_count=summary.transfer_count,
        total_volume=summary.total_volume or Decimal("0"),
        largest_transfer=(
            summary.largest_transfer or Decimal("0")
        ),
        smallest_transfer=(
            summary.smallest_transfer or Decimal("0")
        ),
        unique_addresses=unique_addresses or 0,
    )

async def get_top_addresses(
    session: AsyncSession,
    limit: int = 10,
    chain: str | None = None,
    stablecoin: str | None = None,
    sort_by: str = "transfer_count",
) -> list[TopAddress]:
    conditions = []

    if chain:
        conditions.append(
            StablecoinTransfer.chain == chain
        )

    if stablecoin:
        conditions.append(
            StablecoinTransfer.token_symbol == stablecoin.upper()
        )

    zero_volume = literal(0).cast(
        Numeric(78, 18)
    )

    sent_activity = select(
        StablecoinTransfer.id.label("transfer_id"),
        StablecoinTransfer.from_address.label("address"),
        literal(1).label("sent_count"),
        literal(0).label("received_count"),
        StablecoinTransfer.amount.label("sent_volume"),
        zero_volume.label("received_volume"),
    )

    received_activity = select(
        StablecoinTransfer.id.label("transfer_id"),
        StablecoinTransfer.to_address.label("address"),
        literal(0).label("sent_count"),
        literal(1).label("received_count"),
        zero_volume.label("sent_volume"),
        StablecoinTransfer.amount.label("received_volume"),
    )

    if conditions:
        sent_activity = sent_activity.where(
            *conditions
        )
        received_activity = received_activity.where(
            *conditions
        )

    activity = union_all(
        sent_activity,
        received_activity,
    ).subquery()

    transfer_count = func.count(
        distinct(activity.c.transfer_id)
    )

    sent_count = func.sum(
        activity.c.sent_count
    )

    received_count = func.sum(
        activity.c.received_count
    )

    sent_volume = func.sum(
        activity.c.sent_volume
    )

    received_volume = func.sum(
        activity.c.received_volume
    )

    activity_volume = (
        sent_volume + received_volume
    )

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
            activity.c.address,
            transfer_count.label("transfer_count"),
            sent_count.label("sent_count"),
            received_count.label("received_count"),
            sent_volume.label("sent_volume"),
            received_volume.label("received_volume"),
            activity_volume.label("activity_volume"),
        )
        .group_by(activity.c.address)
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
    stablecoin: str | None = None,
) -> list[DailyVolume]:
    conditions = []

    if chain:
        conditions.append(
            StablecoinTransfer.chain == chain
        )

    if stablecoin:
        conditions.append(
            StablecoinTransfer.token_symbol == stablecoin.upper()
        )

    day = func.date(
        StablecoinTransfer.timestamp
    ).label("date")

    transfer_count = func.count(
        StablecoinTransfer.id
    ).label("transfer_count")

    volume = func.sum(
        StablecoinTransfer.amount
    ).label("volume")

    statement = (
        select(
            day,
            transfer_count,
            volume,
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