from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class StablecoinTransfer(Base):
    __tablename__ = "stablecoin_transfers"
    __table_args__ = (
        UniqueConstraint(
            "chain",
            "transaction_hash",
            "log_index",
            name="uq_transfer_chain_tx_log",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain: Mapped[str] = mapped_column(String(32), index=True)
    token_symbol: Mapped[str] = mapped_column(String(16), index=True)
    token_address: Mapped[str] = mapped_column(String(64), index=True)
    transaction_hash: Mapped[str] = mapped_column(String(80), index=True)
    log_index: Mapped[int] = mapped_column(Integer)
    block_number: Mapped[int] = mapped_column(BigInteger, index=True)
    block_hash: Mapped[str] = mapped_column(String(80))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    from_address: Mapped[str] = mapped_column(String(64), index=True)
    to_address: Mapped[str] = mapped_column(String(64), index=True)
    amount_raw: Mapped[Decimal] = mapped_column(Numeric(78, 0))
    amount: Mapped[Decimal] = mapped_column(Numeric(78, 18), index=True)


class IndexerCheckpoint(Base):
    __tablename__ = "indexer_checkpoints"

    chain: Mapped[str] = mapped_column(String(32), primary_key=True)
    last_processed_block: Mapped[int] = mapped_column(BigInteger)
    last_block_hash: Mapped[str] = mapped_column(String(80))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
