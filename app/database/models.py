import datetime as datetime_module
from datetime import datetime
from decimal import Decimal


from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
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
        Index(
            "ix_transfer_chain_token_event_from_lower",
            "chain",
            "token_symbol",
            "event_type",
            text("lower(from_address)"),
        ),
        Index(
            "ix_transfer_chain_token_event_to_lower",
            "chain",
            "token_symbol",
            "event_type",
            text("lower(to_address)"),
        ),
        Index(
            "ix_transfer_chain_token_event_from_exact",
            "chain",
            "token_symbol",
            "event_type",
            "from_address",
        ),
        Index(
            "ix_transfer_chain_token_event_to_exact",
            "chain",
            "token_symbol",
            "event_type",
            "to_address",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain: Mapped[str] = mapped_column(String(32), index=True)
    token_symbol: Mapped[str] = mapped_column(String(16), index=True)
    token_address: Mapped[str] = mapped_column(String(64), index=True)
    transaction_hash: Mapped[str] = mapped_column(String(128), index=True)
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
    event_type: Mapped[str] = mapped_column(String(16),nullable=False,)


class DailyStablecoinMetric(Base):
    __tablename__ = "daily_stablecoin_metrics"
    __table_args__ = (
        UniqueConstraint(
            "chain",
            "token_symbol",
            "date",
            name="uq_daily_metric_chain_token_date",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain: Mapped[str] = mapped_column(String(32), index=True)
    token_symbol: Mapped[str] = mapped_column(String(16), index=True)
    date: Mapped[datetime_module.date] = mapped_column(index=True)
    transfer_count: Mapped[int] = mapped_column(BigInteger)
    volume: Mapped[Decimal] = mapped_column(Numeric(78, 18))


class ChainTokenMetric(Base):
    __tablename__ = "chain_token_metrics"
    __table_args__ = (
        UniqueConstraint(
            "chain",
            "token_symbol",
            name="uq_chain_token_metric",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain: Mapped[str] = mapped_column(String(32), index=True)
    token_symbol: Mapped[str] = mapped_column(String(16), index=True)
    transfer_count: Mapped[int] = mapped_column(BigInteger)
    total_volume: Mapped[Decimal] = mapped_column(Numeric(78, 18))
    largest_transfer: Mapped[Decimal] = mapped_column(Numeric(78, 18))
    smallest_transfer: Mapped[Decimal] = mapped_column(Numeric(78, 18))


class AddressMetric(Base):
    __tablename__ = "address_metrics"
    __table_args__ = (
        UniqueConstraint(
            "chain",
            "address",
            name="uq_address_metric_chain_address",
        ),
        Index(
            "ix_address_metrics_chain_activity_volume",
            "chain",
            "activity_volume",
        ),
        Index(
            "ix_address_metrics_chain_activity_count",
            "chain",
            "activity_count",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain: Mapped[str] = mapped_column(String(32), index=True)
    address: Mapped[str] = mapped_column(String(64))
    sent_count: Mapped[int] = mapped_column(BigInteger)
    received_count: Mapped[int] = mapped_column(BigInteger)
    activity_count: Mapped[int] = mapped_column(BigInteger)
    sent_volume: Mapped[Decimal] = mapped_column(Numeric(78, 18))
    received_volume: Mapped[Decimal] = mapped_column(Numeric(78, 18))
    activity_volume: Mapped[Decimal] = mapped_column(Numeric(78, 18))


class AddressTokenMetric(Base):
    __tablename__ = "address_token_metrics"
    __table_args__ = (
        UniqueConstraint(
            "chain",
            "address",
            "token_symbol",
            name="uq_address_token_metric",
        ),
        Index(
            "ix_address_token_metrics_chain_token_volume",
            "chain",
            "token_symbol",
            "activity_volume",
        ),
        Index(
            "ix_address_token_metrics_chain_token_count",
            "chain",
            "token_symbol",
            "activity_count",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain: Mapped[str] = mapped_column(String(32), index=True)
    address: Mapped[str] = mapped_column(String(64))
    token_symbol: Mapped[str] = mapped_column(String(16), index=True)
    sent_count: Mapped[int] = mapped_column(BigInteger)
    received_count: Mapped[int] = mapped_column(BigInteger)
    activity_count: Mapped[int] = mapped_column(BigInteger)
    sent_volume: Mapped[Decimal] = mapped_column(Numeric(78, 18))
    received_volume: Mapped[Decimal] = mapped_column(Numeric(78, 18))
    activity_volume: Mapped[Decimal] = mapped_column(Numeric(78, 18))

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

class Watchlist(Base):
    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    addresses: Mapped[list["WatchlistAddress"]] = relationship(
        back_populates="watchlist",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class WatchlistAddress(Base):
    __tablename__ = "watchlist_addresses"

    __table_args__ = (
        UniqueConstraint(
            "watchlist_id",
            "chain",
            "address",
            name="uq_watchlist_chain_address",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    watchlist_id: Mapped[int] = mapped_column(
        ForeignKey(
            "watchlists.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    address: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    label: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    chain: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="base",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    watchlist: Mapped["Watchlist"] = relationship(
        back_populates="addresses",
    )
