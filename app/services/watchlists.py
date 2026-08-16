from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import (and_, case, delete, func, or_, select)

from app.database.models import Watchlist, WatchlistAddress, StablecoinTransfer


class WatchlistNotFoundError(Exception):
    pass


class DuplicateWatchlistAddressError(Exception):
    pass


def normalize_address(
    address: str,
    chain: str,
) -> str:
    normalized = address.strip()

    if chain == "base-sepolia":
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

async def get_watchlist_analytics(
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

    is_sender = (
        func.lower(StablecoinTransfer.from_address)
        == func.lower(watched.c.address)
    )

    is_receiver = (
        func.lower(StablecoinTransfer.to_address)
        == func.lower(watched.c.address)
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

    partner_address = case(
        (
            is_sender,
            func.lower(
                StablecoinTransfer.to_address,
            ),
        ),
        else_=func.lower(
            StablecoinTransfer.from_address,
        ),
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