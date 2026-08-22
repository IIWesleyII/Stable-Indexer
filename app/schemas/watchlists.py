from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from pydantic import field_serializer

class WatchlistCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )


class WatchlistAddressCreate(BaseModel):
    address: str = Field(
        min_length=1,
        max_length=128,
    )

    label: str | None = Field(
        default=None,
        max_length=100,
    )

    chain: str = Field(
        default="base",
        min_length=1,
        max_length=32,
    )


class WatchlistAddressResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    address: str
    label: str | None
    chain: str
    created_at: datetime


class WatchlistResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    name: str
    created_at: datetime


class WatchlistDetailResponse(WatchlistResponse):
    addresses: list[WatchlistAddressResponse]


class WatchlistAddressAnalytics(BaseModel):
    id: int
    address: str
    label: str | None
    chain: str
    transfer_count: int
    sent_count: int
    received_count: int
    sent_volume: Decimal
    received_volume: Decimal
    net_flow: Decimal
    unique_partners: int
    last_activity: datetime | None

    @field_serializer(
        "sent_volume",
        "received_volume",
        "net_flow",
    )
    def serialize_volume(
        self,
        value: Decimal,
    ) -> str:
        return f"{value:.6f}"
