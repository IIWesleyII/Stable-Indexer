from decimal import Decimal

from sqlalchemy import case
from sqlalchemy import distinct
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy import literal
from sqlalchemy import Numeric
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import StablecoinTransfer
from app.schemas.addresses import AddressSummary
from app.schemas.addresses import AddressPartner

async def get_address_summary(
    session: AsyncSession,
    address: str,
    chain: str | None = None,
    stablecoin: str | None = None,
) -> AddressSummary | None:
    normalized_address = address.lower()

    is_sender = (
        func.lower(StablecoinTransfer.from_address)
        == normalized_address
    )

    is_receiver = (
        func.lower(StablecoinTransfer.to_address)
        == normalized_address
    )

    conditions = [
        StablecoinTransfer.event_type == "transfer",
        or_(
            is_sender,
            is_receiver,
        ),
    ]

    if chain:
        conditions.append(
            StablecoinTransfer.chain == chain
        )

    if stablecoin:
        conditions.append(
            StablecoinTransfer.token_symbol
            == stablecoin.upper()
        )

    statement = (
        select(
            func.count(
                StablecoinTransfer.id
            ).label("transfer_count"),
            func.sum(
                case(
                    (is_sender, 1),
                    else_=0,
                )
            ).label("sent_count"),
            func.sum(
                case(
                    (is_receiver, 1),
                    else_=0,
                )
            ).label("received_count"),
            func.sum(
                case(
                    (
                        is_sender,
                        StablecoinTransfer.amount,
                    ),
                    else_=0,
                )
            ).label("sent_volume"),
            func.sum(
                case(
                    (
                        is_receiver,
                        StablecoinTransfer.amount,
                    ),
                    else_=0,
                )
            ).label("received_volume"),
            func.min(
                StablecoinTransfer.timestamp
            ).label("first_activity"),
            func.max(
                StablecoinTransfer.timestamp
            ).label("last_activity"),
        )
        .where(*conditions)
    )

    result = await session.execute(statement)
    summary = result.one()

    if summary.transfer_count == 0:
        return None

    partner_address = case(
        (
            is_sender,
            StablecoinTransfer.to_address,
        ),
        else_=StablecoinTransfer.from_address,
    )

    partner_statement = (
        select(
            func.count(
                distinct(partner_address)
            )
        )
        .where(
            *conditions,
            func.lower(partner_address)
            != normalized_address,
        )
    )

    unique_partners = await session.scalar(
        partner_statement
    )

    sent_volume = summary.sent_volume or Decimal("0")
    received_volume = summary.received_volume or Decimal("0")

    return AddressSummary(
        address=address,
        transfer_count=summary.transfer_count,
        sent_count=summary.sent_count or 0,
        received_count=summary.received_count or 0,
        sent_volume=sent_volume,
        received_volume=received_volume,
        net_flow=received_volume - sent_volume,
        unique_partners=unique_partners or 0,
        first_activity=summary.first_activity,
        last_activity=summary.last_activity,
    )

async def get_address_partners(
    session: AsyncSession,
    address: str,
    limit: int = 10,
    sort_by: str = "transfer_count",
    chain: str | None = None,
    stablecoin: str | None = None,
) -> list[AddressPartner]:
    normalized_address = address.lower()

    is_sender = (
        func.lower(StablecoinTransfer.from_address)
        == normalized_address
    )

    is_receiver = (
        func.lower(StablecoinTransfer.to_address)
        == normalized_address
    )

    conditions = [
        StablecoinTransfer.event_type == "transfer",
        or_(
            is_sender,
            is_receiver,
        ),
    ]

    if chain:
        conditions.append(
            StablecoinTransfer.chain == chain
        )

    if stablecoin:
        conditions.append(
            StablecoinTransfer.token_symbol
            == stablecoin.upper()
        )

    partner_address = case(
        (
            is_sender,
            StablecoinTransfer.to_address,
        ),
        else_=StablecoinTransfer.from_address,
    )

    zero_volume = literal(0).cast(
        Numeric(78, 18)
    )

    sent_count = func.sum(
        case(
            (is_sender, 1),
            else_=0,
        )
    )

    received_count = func.sum(
        case(
            (is_receiver, 1),
            else_=0,
        )
    )

    sent_volume = func.sum(
        case(
            (
                is_sender,
                StablecoinTransfer.amount,
            ),
            else_=zero_volume,
        )
    )

    received_volume = func.sum(
        case(
            (
                is_receiver,
                StablecoinTransfer.amount,
            ),
            else_=zero_volume,
        )
    )

    transfer_count = func.count(
        StablecoinTransfer.id
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
            partner_address.label("address"),
            transfer_count.label("transfer_count"),
            sent_count.label("sent_count"),
            received_count.label("received_count"),
            sent_volume.label("sent_volume"),
            received_volume.label("received_volume"),
            activity_volume.label("activity_volume"),
        )
        .where(
            *conditions,
            func.lower(partner_address)
            != normalized_address,
        )
        .group_by(partner_address)
        .order_by(*order_by)
        .limit(limit)
    )

    result = await session.execute(statement)

    return [
        AddressPartner(**row)
        for row in result.mappings().all()
    ]