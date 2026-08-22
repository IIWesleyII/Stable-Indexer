from sqlalchemy import and_
from sqlalchemy import case
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AddressMetric
from app.database.models import AddressTokenMetric
from app.database.models import ChainTokenMetric
from app.database.models import DailyStablecoinMetric
from app.schemas.metrics import DailyVolume
from app.schemas.metrics import MetricsSummary
from app.schemas.metrics import TopAddress


def metric_conditions(
    model,
    chain: str | None,
    stablecoin: str | None,
) -> list:
    conditions = []

    if chain is not None:
        conditions.append(model.chain == chain)

    if stablecoin is not None:
        conditions.append(model.token_symbol == stablecoin)

    return conditions


async def get_summary_metrics(
    session: AsyncSession,
    chain: str | None = None,
    stablecoin: str | None = None,
) -> MetricsSummary:
    summary_conditions = metric_conditions(
        ChainTokenMetric,
        chain,
        stablecoin,
    )
    summary_statement = select(
        func.coalesce(
            func.sum(ChainTokenMetric.transfer_count),
            0,
        ).label("transfer_count"),
        func.coalesce(
            func.sum(ChainTokenMetric.total_volume),
            0,
        ).label("total_volume"),
        func.coalesce(
            func.max(ChainTokenMetric.largest_transfer),
            0,
        ).label("largest_transfer"),
        func.coalesce(
            func.min(ChainTokenMetric.smallest_transfer),
            0,
        ).label("smallest_transfer"),
    ).where(*summary_conditions)
    summary_result = await session.execute(summary_statement)
    summary = summary_result.one()

    address_model = (
        AddressTokenMetric
        if stablecoin is not None
        else AddressMetric
    )
    address_conditions = metric_conditions(
        address_model,
        chain,
        stablecoin,
    )
    unique_statement = select(
        func.count(address_model.id).label("unique_addresses")
    ).where(*address_conditions)
    unique_result = await session.execute(unique_statement)

    return MetricsSummary(
        transfer_count=summary.transfer_count,
        total_volume=summary.total_volume,
        largest_transfer=summary.largest_transfer,
        smallest_transfer=summary.smallest_transfer,
        unique_addresses=unique_result.scalar_one(),
    )


async def get_top_addresses(
    session: AsyncSession,
    limit: int = 10,
    sort_by: str = "volume",
    chain: str | None = None,
    stablecoin: str | None = None,
) -> list[TopAddress]:
    metric_model = (
        AddressTokenMetric
        if stablecoin is not None
        else AddressMetric
    )
    conditions = metric_conditions(
        metric_model,
        chain,
        stablecoin,
    )
    order_column = (
        metric_model.activity_volume
        if sort_by == "volume"
        else metric_model.activity_count
    )

    ranked = (
        select(
            metric_model.chain,
            metric_model.address,
            metric_model.sent_count,
            metric_model.received_count,
            metric_model.activity_count,
            metric_model.sent_volume,
            metric_model.received_volume,
            metric_model.activity_volume,
        )
        .where(*conditions)
        .order_by(
            order_column.desc(),
            metric_model.activity_count.desc(),
        )
        .limit(limit)
        .cte("ranked_addresses")
    )

    token_conditions = [
        AddressTokenMetric.chain == ranked.c.chain,
        AddressTokenMetric.address == ranked.c.address,
    ]
    if stablecoin is not None:
        token_conditions.append(
            AddressTokenMetric.token_symbol == stablecoin
        )

    token_totals = (
        select(
            AddressTokenMetric.chain.label("chain"),
            AddressTokenMetric.address.label("address"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            AddressTokenMetric.token_symbol == "USDC",
                            AddressTokenMetric.activity_volume,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("usdc_activity_volume"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            AddressTokenMetric.token_symbol == "USDT",
                            AddressTokenMetric.activity_volume,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("usdt_activity_volume"),
        )
        .where(*token_conditions)
        .group_by(
            AddressTokenMetric.chain,
            AddressTokenMetric.address,
        )
        .subquery()
    )

    statement = (
        select(
            ranked.c.chain,
            ranked.c.address,
            ranked.c.activity_count.label("transfer_count"),
            ranked.c.sent_count,
            ranked.c.received_count,
            ranked.c.sent_volume,
            ranked.c.received_volume,
            ranked.c.activity_volume,
            func.coalesce(
                token_totals.c.usdc_activity_volume,
                0,
            ).label("usdc_activity_volume"),
            func.coalesce(
                token_totals.c.usdt_activity_volume,
                0,
            ).label("usdt_activity_volume"),
        )
        .outerjoin(
            token_totals,
            and_(
                token_totals.c.chain == ranked.c.chain,
                token_totals.c.address == ranked.c.address,
            ),
        )
        .order_by(
            ranked.c.activity_volume.desc()
            if sort_by == "volume"
            else ranked.c.activity_count.desc(),
            ranked.c.activity_count.desc(),
        )
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
    conditions = metric_conditions(
        DailyStablecoinMetric,
        chain,
        stablecoin,
    )
    recent_days = (
        select(DailyStablecoinMetric.date)
        .where(*conditions)
        .group_by(DailyStablecoinMetric.date)
        .order_by(DailyStablecoinMetric.date.desc())
        .limit(days)
        .subquery()
    )
    statement = (
        select(
            DailyStablecoinMetric.date,
            DailyStablecoinMetric.token_symbol,
            DailyStablecoinMetric.transfer_count,
            DailyStablecoinMetric.volume,
        )
        .where(*conditions)
        .where(
            DailyStablecoinMetric.date.in_(
                select(recent_days.c.date)
            )
        )
        .order_by(
            DailyStablecoinMetric.date,
            DailyStablecoinMetric.token_symbol,
        )
    )
    result = await session.execute(statement)

    return [
        DailyVolume(**row)
        for row in result.mappings().all()
    ]
