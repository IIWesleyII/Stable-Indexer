from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class TransferRead(BaseModel):
    id: int = Field(examples=[1])
    chain: str = Field(examples=["base"])
    token_symbol: str = Field(examples=["USDC"])
    token_address: str = Field(
        examples=["0x036CbD53842c5426634e7929541eC2318f3dCF7e"]
    )
    transaction_hash: str = Field(examples=["0x1234567890abcdef"])
    log_index: int = Field(examples=[12])
    block_number: int = Field(examples=[20000084])
    block_hash: str = Field(examples=["0xabcdef1234567890"])
    timestamp: datetime = Field(examples=["2026-08-12T18:30:35.550Z"])
    from_address: str = Field(
        examples=["0x1111111111111111111111111111111111111111"]
    )
    to_address: str = Field(
        examples=["0x2222222222222222222222222222222222222222"]
    )
    amount_raw: int = Field(examples=[25000000])
    amount: Decimal = Field(examples=["25.000000"])

    model_config = ConfigDict(from_attributes=True)


class ScanRequest(BaseModel):
    from_block: int = Field(ge=0)
    to_block: int = Field(ge=0)


class ScanResult(BaseModel):
    from_block: int
    to_block: int
    discovered: int
    inserted: int


class LatestBlockRead(BaseModel):
    chain: str
    block_number: int


class SyncRequest(BaseModel):
    start_block: int | None = Field(default=None, ge=0)
    max_blocks: int = Field(default=2000, ge=1, le=10000)


class SyncResult(BaseModel):
    chain: str
    from_block: int | None
    to_block: int | None
    latest_block: int
    discovered: int
    inserted: int
    batches: int
    caught_up: bool


class CheckpointRead(BaseModel):
    chain: str
    last_processed_block: int
    last_block_hash: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
