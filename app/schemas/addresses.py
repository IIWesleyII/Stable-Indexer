from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_serializer


class AddressSummary(BaseModel):
    address: str = Field(
        examples=["0x3Ac0bf9c221bE330c84d7120804513591F481d8D"]
    )
    transfer_count: int = Field(examples=[29828])
    sent_count: int = Field(examples=[29828])
    received_count: int = Field(examples=[0])
    sent_volume: Decimal = Field(examples=["32.870000"])
    received_volume: Decimal = Field(examples=["0.000000"])
    net_flow: Decimal = Field(examples=["-32.870000"])
    unique_partners: int = Field(examples=[42])
    first_activity: datetime
    last_activity: datetime

    @field_serializer(
        "sent_volume",
        "received_volume",
        "net_flow",
    )
    def serialize_volume(self, value: Decimal) -> str:
        # keep it to USDC 6 decimal standard
        return f"{value:.6f}"

class AddressPartner(BaseModel):
    address: str
    transfer_count: int
    sent_count: int
    received_count: int
    sent_volume: Decimal
    received_volume: Decimal
    activity_volume: Decimal

    @field_serializer(
        "sent_volume",
        "received_volume",
        "activity_volume",
    )
    def serialize_volume(self, value: Decimal) -> str:
        return f"{value:.6f}"