from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AddressMetric
from app.database.models import AddressTokenMetric
from app.database.models import ChainTokenMetric
from app.database.models import DailyStablecoinMetric


TRANSFER_EVENT_TYPE = "transfer"
CASE_SENSITIVE_ADDRESS_CHAINS = {"solana", "tron"}


def normalize_address(address: str, chain: str) -> str:
    if chain in CASE_SENSITIVE_ADDRESS_CHAINS:
        return address

    return address.lower()


def build_rollup_rows(
    transfers: Iterable[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    daily: dict[tuple[str, str, date], dict[str, Any]] = {}
    chain_tokens: dict[tuple[str, str], dict[str, Any]] = {}
    addresses: dict[tuple[str, str], dict[str, Any]] = {}
    address_tokens: dict[tuple[str, str, str], dict[str, Any]] = {}

    for transfer in transfers:
        if transfer["event_type"] != TRANSFER_EVENT_TYPE:
            continue

        chain = transfer["chain"]
        token_symbol = transfer["token_symbol"]
        amount = Decimal(transfer["amount"])
        transfer_date = transfer["timestamp"].date()

        daily_key = (chain, token_symbol, transfer_date)
        daily_row = daily.setdefault(
            daily_key,
            {
                "chain": chain,
                "token_symbol": token_symbol,
                "date": transfer_date,
                "transfer_count": 0,
                "volume": Decimal(0),
            },
        )
        daily_row["transfer_count"] += 1
        daily_row["volume"] += amount

        chain_token_key = (chain, token_symbol)
        chain_token_row = chain_tokens.setdefault(
            chain_token_key,
            {
                "chain": chain,
                "token_symbol": token_symbol,
                "transfer_count": 0,
                "total_volume": Decimal(0),
                "largest_transfer": amount,
                "smallest_transfer": amount,
            },
        )
        chain_token_row["transfer_count"] += 1
        chain_token_row["total_volume"] += amount
        chain_token_row["largest_transfer"] = max(
            chain_token_row["largest_transfer"],
            amount,
        )
        chain_token_row["smallest_transfer"] = min(
            chain_token_row["smallest_transfer"],
            amount,
        )

        for direction, raw_address in (
            ("sent", transfer["from_address"]),
            ("received", transfer["to_address"]),
        ):
            address = normalize_address(raw_address, chain)
            address_key = (chain, address)
            address_row = addresses.setdefault(
                address_key,
                {
                    "chain": chain,
                    "address": address,
                    "sent_count": 0,
                    "received_count": 0,
                    "activity_count": 0,
                    "sent_volume": Decimal(0),
                    "received_volume": Decimal(0),
                    "activity_volume": Decimal(0),
                },
            )
            address_token_key = (chain, address, token_symbol)
            address_token_row = address_tokens.setdefault(
                address_token_key,
                {
                    **address_row,
                    "token_symbol": token_symbol,
                    "sent_count": 0,
                    "received_count": 0,
                    "activity_count": 0,
                    "sent_volume": Decimal(0),
                    "received_volume": Decimal(0),
                    "activity_volume": Decimal(0),
                },
            )

            for row in (address_row, address_token_row):
                row[f"{direction}_count"] += 1
                row[f"{direction}_volume"] += amount
                row["activity_count"] += 1
                row["activity_volume"] += amount

    return (
        list(daily.values()),
        list(chain_tokens.values()),
        list(addresses.values()),
        list(address_tokens.values()),
    )


async def update_metric_rollups(
    session: AsyncSession,
    transfers: Iterable[dict[str, Any]],
) -> None:
    (
        daily_rows,
        chain_token_rows,
        address_rows,
        address_token_rows,
    ) = build_rollup_rows(transfers)

    if daily_rows:
        statement = insert(DailyStablecoinMetric).values(daily_rows)
        await session.execute(
            statement.on_conflict_do_update(
                constraint="uq_daily_metric_chain_token_date",
                set_={
                    "transfer_count": (
                        DailyStablecoinMetric.transfer_count
                        + statement.excluded.transfer_count
                    ),
                    "volume": (
                        DailyStablecoinMetric.volume
                        + statement.excluded.volume
                    ),
                },
            )
        )

    if chain_token_rows:
        statement = insert(ChainTokenMetric).values(chain_token_rows)
        await session.execute(
            statement.on_conflict_do_update(
                constraint="uq_chain_token_metric",
                set_={
                    "transfer_count": (
                        ChainTokenMetric.transfer_count
                        + statement.excluded.transfer_count
                    ),
                    "total_volume": (
                        ChainTokenMetric.total_volume
                        + statement.excluded.total_volume
                    ),
                    "largest_transfer": func.greatest(
                        ChainTokenMetric.largest_transfer,
                        statement.excluded.largest_transfer,
                    ),
                    "smallest_transfer": func.least(
                        ChainTokenMetric.smallest_transfer,
                        statement.excluded.smallest_transfer,
                    ),
                },
            )
        )

    for model, rows, constraint in (
        (
            AddressMetric,
            address_rows,
            "uq_address_metric_chain_address",
        ),
        (
            AddressTokenMetric,
            address_token_rows,
            "uq_address_token_metric",
        ),
    ):
        if not rows:
            continue

        statement = insert(model).values(rows)
        await session.execute(
            statement.on_conflict_do_update(
                constraint=constraint,
                set_={
                    "sent_count": (
                        model.sent_count + statement.excluded.sent_count
                    ),
                    "received_count": (
                        model.received_count
                        + statement.excluded.received_count
                    ),
                    "activity_count": (
                        model.activity_count
                        + statement.excluded.activity_count
                    ),
                    "sent_volume": (
                        model.sent_volume + statement.excluded.sent_volume
                    ),
                    "received_volume": (
                        model.received_volume
                        + statement.excluded.received_volume
                    ),
                    "activity_volume": (
                        model.activity_volume
                        + statement.excluded.activity_volume
                    ),
                },
            )
        )
