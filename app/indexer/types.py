from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class IndexedTransfer:
    chain: str
    token_symbol: str
    token_address: str
    transaction_hash: str
    log_index: int
    block_number: int
    block_hash: str
    timestamp: datetime
    from_address: str
    to_address: str
    amount_raw: Decimal
    amount: Decimal
    event_type: str