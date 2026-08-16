from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.schemas.watchlists import (
    WatchlistAddressAnalytics,
    WatchlistAddressCreate,
    WatchlistAddressResponse,
    WatchlistCreate,
    WatchlistDetailResponse,
    WatchlistResponse,
)
from app.services.watchlists import (
    DuplicateWatchlistAddressError,
    WatchlistNotFoundError,
    add_watchlist_address,
    create_watchlist,
    get_watchlist,
    get_watchlist_analytics,
    get_watchlists,
    remove_watchlist_address,
)


router = APIRouter(
    prefix="/watchlists",
    tags=["watchlists"],
)


@router.get(
    "",
    response_model=list[WatchlistResponse],
)
async def list_watchlists(
    session: AsyncSession = Depends(
        get_session,
    ),
) -> list[WatchlistResponse]:
    return await get_watchlists(
        session,
    )


@router.post(
    "",
    response_model=WatchlistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_watchlist(
    request: WatchlistCreate,
    session: AsyncSession = Depends(
        get_session,
    ),
) -> WatchlistResponse:
    return await create_watchlist(
        session,
        request.name,
    )


@router.get(
    "/{watchlist_id}",
    response_model=WatchlistDetailResponse,
)
async def get_watchlist_detail(
    watchlist_id: int,
    session: AsyncSession = Depends(
        get_session,
    ),
) -> WatchlistDetailResponse:
    watchlist = await get_watchlist(
        session,
        watchlist_id,
    )

    if watchlist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )

    return watchlist


@router.post(
    "/{watchlist_id}/addresses",
    response_model=WatchlistAddressResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_address(
    watchlist_id: int,
    request: WatchlistAddressCreate,
    session: AsyncSession = Depends(
        get_session,
    ),
) -> WatchlistAddressResponse:
    try:
        return await add_watchlist_address(
            session=session,
            watchlist_id=watchlist_id,
            address=request.address,
            chain=request.chain,
            label=request.label,
        )
    except WatchlistNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        ) from error
    except DuplicateWatchlistAddressError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Address is already in this watchlist",
        ) from error


@router.delete(
    "/{watchlist_id}/addresses/{address}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_address(
    watchlist_id: int,
    address: str,
    chain: str = "base-sepolia",
    session: AsyncSession = Depends(
        get_session,
    ),
) -> Response:
    deleted = await remove_watchlist_address(
        session=session,
        watchlist_id=watchlist_id,
        address=address,
        chain=chain,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist address not found",
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )

@router.get(
    "/{watchlist_id}/analytics",
    response_model=list[WatchlistAddressAnalytics],
)
async def get_analytics(
    watchlist_id: int,
    stablecoin: str = "USDC",
    session: AsyncSession = Depends(
        get_session,
    ),
) -> list[WatchlistAddressAnalytics]:
    try:
        return await get_watchlist_analytics(
            session=session,
            watchlist_id=watchlist_id,
            stablecoin=stablecoin,
        )
    except WatchlistNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        ) from error