from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import (
    and_,
    case,
    delete,
    func,
    literal,
    or_,
    select,
    union_all,
)

from app.database.models import Watchlist, WatchlistAddress, StablecoinTransfer


class WatchlistNotFoundError(Exception):
    pass


class DuplicateWatchlistAddressError(Exception):
    pass


EVM_CHAINS = (
    "base",
    "ethereum",
)
CASE_SENSITIVE_ADDRESS_CHAINS = (
    "solana",
    "tron",
)


def normalize_address(
    address: str,
    chain: str,
) -> str:
    normalized = address.strip()

    if chain in {
        "base",
        "ethereum",
    }:
        return normalized.lower()

    return normalized


async def get_watchlists(
    session: AsyncSession,
) -> list[Watchlist]:
    statement = select(Watchlist).order_by(
        Watchlist.created_at,
    )

    result = await session.execute(statement)

    return list(result.scalars().all())


async def create_watchlist(
    session: AsyncSession,
    name: str,
) -> Watchlist:
    watchlist = Watchlist(
        name=name.strip(),
    )

    session.add(watchlist)

    await session.commit()
    await session.refresh(watchlist)

    return watchlist


async def get_watchlist(
    session: AsyncSession,
    watchlist_id: int,
) -> Watchlist | None:
    statement = (
        select(Watchlist)
        .options(
            selectinload(
                Watchlist.addresses,
            )
        )
        .where(
            Watchlist.id == watchlist_id,
        )
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def add_watchlist_address(
    session: AsyncSession,
    watchlist_id: int,
    address: str,
    chain: str,
    label: str | None,
) -> WatchlistAddress:
    watchlist = await session.get(
        Watchlist,
        watchlist_id,
    )

    if watchlist is None:
        raise WatchlistNotFoundError

    normalized_address = normalize_address(
        address,
        chain,
    )

    watchlist_address = WatchlistAddress(
        watchlist_id=watchlist_id,
        address=normalized_address,
        chain=chain,
        label=label.strip() if label else None,
    )

    session.add(watchlist_address)

    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()

        raise DuplicateWatchlistAddressError from error

    await session.refresh(
        watchlist_address,
    )

    return watchlist_address


async def remove_watchlist_address(
    session: AsyncSession,
    watchlist_id: int,
    address: str,
    chain: str,
) -> bool:
    normalized_address = normalize_address(
        address,
        chain,
    )

    statement = (
        delete(WatchlistAddress)
        .where(
            WatchlistAddress.watchlist_id
            == watchlist_id,
        )
        .where(
            WatchlistAddress.chain == chain,
        )
        .where(
            WatchlistAddress.address
            == normalized_address,
        )
        .returning(
            WatchlistAddress.id,
        )
    )

    result = await session.execute(statement)
    deleted_id = result.scalar_one_or_none()

    if deleted_id is None:
        await session.rollback()
        return False

    await session.commit()

    return True

async def get_watchlist_analytics_legacy(
    session: AsyncSession,
    watchlist_id: int,
    stablecoin: str = "USDC",
) -> list[dict]:
    watchlist = await session.get(
        Watchlist,
        watchlist_id,
    )

    if watchlist is None:
        raise WatchlistNotFoundError

    watched = (
        select(
            WatchlistAddress.id.label("id"),
            WatchlistAddress.address.label("address"),
            WatchlistAddress.label.label("label"),
            WatchlistAddress.chain.label("chain"),
        )
        .where(
            WatchlistAddress.watchlist_id == watchlist_id,
        )
        .subquery()
    )

    is_sender = or_(
        and_(
            watched.c.chain.in_(CASE_SENSITIVE_ADDRESS_CHAINS),
            StablecoinTransfer.from_address == watched.c.address,
        ),
        and_(
            watched.c.chain.not_in(CASE_SENSITIVE_ADDRESS_CHAINS),
            func.lower(StablecoinTransfer.from_address)
            == func.lower(watched.c.address),
        ),
    )

    is_receiver = or_(
        and_(
            watched.c.chain.in_(CASE_SENSITIVE_ADDRESS_CHAINS),
            StablecoinTransfer.to_address == watched.c.address,
        ),
        and_(
            watched.c.chain.not_in(CASE_SENSITIVE_ADDRESS_CHAINS),
            func.lower(StablecoinTransfer.to_address)
            == func.lower(watched.c.address),
        ),
    )

    sent_count = func.coalesce(
        func.sum(
            case(
                (is_sender, 1),
                else_=0,
            )
        ),
        0,
    )

    received_count = func.coalesce(
        func.sum(
            case(
                (is_receiver, 1),
                else_=0,
            )
        ),
        0,
    )

    sent_volume = func.coalesce(
        func.sum(
            case(
                (
                    is_sender,
                    StablecoinTransfer.amount,
                ),
                else_=0,
            )
        ),
        0,
    )

    received_volume = func.coalesce(
        func.sum(
            case(
                (
                    is_receiver,
                    StablecoinTransfer.amount,
                ),
                else_=0,
            )
        ),
        0,
    )

    raw_partner_address = case(
        (
            is_sender,
            StablecoinTransfer.to_address,
        ),
        else_=StablecoinTransfer.from_address,
    )

    partner_address = case(
        (
            watched.c.chain.in_(CASE_SENSITIVE_ADDRESS_CHAINS),
            raw_partner_address,
        ),
            else_=func.lower(raw_partner_address),
    )

    join_condition = and_(
        StablecoinTransfer.chain == watched.c.chain,
        StablecoinTransfer.token_symbol == stablecoin,
        StablecoinTransfer.event_type == "transfer",
        or_(
            is_sender,
            is_receiver,
        ),
    )

    statement = (
        select(
            watched.c.id,
            watched.c.address,
            watched.c.label,
            watched.c.chain,
            func.count(
                StablecoinTransfer.id,
            ).label("transfer_count"),
            sent_count.label("sent_count"),
            received_count.label(
                "received_count",
            ),
            sent_volume.label("sent_volume"),
            received_volume.label(
                "received_volume",
            ),
            (
                received_volume - sent_volume
            ).label("net_flow"),
            func.count(
                func.distinct(partner_address),
            ).label("unique_partners"),
            func.max(
                StablecoinTransfer.timestamp,
            ).label("last_activity"),
        )
        .select_from(watched)
        .outerjoin(
            StablecoinTransfer,
            join_condition,
        )
        .group_by(
            watched.c.id,
            watched.c.address,
            watched.c.label,
            watched.c.chain,
        )
        .order_by(
            func.max(
                StablecoinTransfer.timestamp,
            ).desc().nullslast(),
            watched.c.id,
        )
    )

    result = await session.execute(statement)

    return [
        dict(row)
        for row in result.mappings().all()
    ]


async def get_watchlist_analytics(
    session: AsyncSession,
    watchlist_id: int,
    stablecoin: str | None = None,
) -> list[dict]:
    watchlist = await session.get(Watchlist, watchlist_id)

    if watchlist is None:
        raise WatchlistNotFoundError

    watched = (
        select(
            WatchlistAddress.id.label("id"),
            WatchlistAddress.address.label("address"),
            WatchlistAddress.label.label("label"),
            WatchlistAddress.chain.label("chain"),
        )
        .where(WatchlistAddress.watchlist_id == watchlist_id)
        .subquery()
    )

    def activity_select(
        address_column,
        partner_column,
        sent: int,
        received: int,
        evm: bool,
    ):
        address_match = (
            func.lower(address_column) == watched.c.address
            if evm
            else address_column == watched.c.address
        )
        chain_condition = (
            watched.c.chain.in_(EVM_CHAINS)
            if evm
            else watched.c.chain.not_in(EVM_CHAINS)
        )
        partner = (
            func.lower(partner_column)
            if evm
            else partner_column
        )

        transfer_conditions = [
            chain_condition,
            StablecoinTransfer.chain == watched.c.chain,
            StablecoinTransfer.event_type == "transfer",
            address_match,
        ]

        if stablecoin:
            transfer_conditions.append(
                StablecoinTransfer.token_symbol == stablecoin.upper()
            )

        return (
            select(
                watched.c.id.label("watchlist_address_id"),
                StablecoinTransfer.id.label("transfer_id"),
                partner.label("partner_address"),
                StablecoinTransfer.timestamp.label("timestamp"),
                literal(sent).label("sent_count"),
                literal(received).label("received_count"),
                case(
                    (sent == 1, StablecoinTransfer.amount),
                    else_=0,
                ).label("sent_volume"),
                case(
                    (received == 1, StablecoinTransfer.amount),
                    else_=0,
                ).label("received_volume"),
            )
            .select_from(watched)
            .join(
                StablecoinTransfer,
                and_(*transfer_conditions),
            )
        )

    activity = union_all(
        activity_select(
            StablecoinTransfer.from_address,
            StablecoinTransfer.to_address,
            sent=1,
            received=0,
            evm=True,
        ),
        activity_select(
            StablecoinTransfer.to_address,
            StablecoinTransfer.from_address,
            sent=0,
            received=1,
            evm=True,
        ),
        activity_select(
            StablecoinTransfer.from_address,
            StablecoinTransfer.to_address,
            sent=1,
            received=0,
            evm=False,
        ),
        activity_select(
            StablecoinTransfer.to_address,
            StablecoinTransfer.from_address,
            sent=0,
            received=1,
            evm=False,
        ),
    ).subquery()

    sent_count = func.coalesce(func.sum(activity.c.sent_count), 0)
    received_count = func.coalesce(
        func.sum(activity.c.received_count),
        0,
    )
    sent_volume = func.coalesce(func.sum(activity.c.sent_volume), 0)
    received_volume = func.coalesce(
        func.sum(activity.c.received_volume),
        0,
    )

    statement = (
        select(
            watched.c.id,
            watched.c.address,
            watched.c.label,
            watched.c.chain,
            func.count(func.distinct(activity.c.transfer_id)).label(
                "transfer_count"
            ),
            sent_count.label("sent_count"),
            received_count.label("received_count"),
            sent_volume.label("sent_volume"),
            received_volume.label("received_volume"),
            (received_volume - sent_volume).label("net_flow"),
            func.count(
                func.distinct(activity.c.partner_address)
            ).label("unique_partners"),
            func.max(activity.c.timestamp).label("last_activity"),
        )
        .select_from(watched)
        .outerjoin(
            activity,
            activity.c.watchlist_address_id == watched.c.id,
        )
        .group_by(
            watched.c.id,
            watched.c.address,
            watched.c.label,
            watched.c.chain,
        )
        .order_by(
            func.max(activity.c.timestamp).desc().nullslast(),
            watched.c.id,
        )
    )
    result = await session.execute(statement)

    return [
        dict(row)
        for row in result.mappings().all()
    ]
