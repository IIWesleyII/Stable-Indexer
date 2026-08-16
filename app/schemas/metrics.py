from decimal import Decimal
from datetime import date
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_serializer

class MetricsSummary(BaseModel):
    transfer_count: int = Field(examples=[5421])
    total_volume: Decimal = Field(examples=["18429102.52"])
    largest_transfer: Decimal = Field(examples=["1250000.00"])
    smallest_transfer: Decimal = Field(examples=["0.001"])
    unique_addresses: int = Field(examples=[2184])

class TopAddress(BaseModel):
    chain: str
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
        # keep it to USDC 6 decimal standard
        return f"{value:.6f}"

class DailyVolume(BaseModel):
    date: date
    transfer_count: int
    volume: Decimal

    @field_serializer("volume")
    def serialize_volume(self, value: Decimal) -> str:
        return f"{value:.6f}"