from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from typing import Literal
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.schemas.addresses import AddressSummary
from app.services.addresses import get_address_summary

from app.schemas.addresses import AddressPartner
from app.services.addresses import get_address_partners

router = APIRouter(
    prefix="/addresses",
    tags=["addresses"],
)


@router.get(
    "/{address}",
    response_model=AddressSummary,
)
async def address_summary(
    address: str,
    chain: str | None = None,
    stablecoin: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> AddressSummary:
    summary = await get_address_summary(
        session=session,
        address=address,
        chain=chain,
        stablecoin=stablecoin,
    )

    if summary is None:
        raise HTTPException(
            status_code=404,
            detail="No indexed activity found for this address.",
        )

    return summary

@router.get(
    "/{address}/partners",
    response_model=list[AddressPartner],
)
async def address_partners(
    address: str,
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
) -> list[AddressPartner]:
    return await get_address_partners(
        session=session,
        address=address,
        limit=limit,
        sort_by=sort_by,
        chain=chain,
        stablecoin=stablecoin,
    )