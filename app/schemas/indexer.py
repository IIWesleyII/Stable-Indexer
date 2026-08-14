from datetime import datetime

from pydantic import BaseModel


class IndexerStatus(BaseModel):
    chain: str
    latest_block: int
    last_processed_block: int | None
    blocks_behind: int | None
    caught_up: bool
    updated_at: datetime | None