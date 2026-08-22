from datetime import datetime
from datetime import timezone
from decimal import Decimal
from unittest import TestCase

from app.services.metric_rollups import build_rollup_rows


class MetricRollupTests(TestCase):
    def test_groups_daily_and_address_activity_by_token(self) -> None:
        transfers = [
            {
                "chain": "base",
                "token_symbol": "USDC",
                "timestamp": datetime(2026, 8, 20, tzinfo=timezone.utc),
                "from_address": "0xAbC",
                "to_address": "0xDef",
                "amount": Decimal("12.5"),
                "event_type": "transfer",
            },
            {
                "chain": "base",
                "token_symbol": "USDT",
                "timestamp": datetime(2026, 8, 20, tzinfo=timezone.utc),
                "from_address": "0xabc",
                "to_address": "0xDef",
                "amount": Decimal("7.5"),
                "event_type": "transfer",
            },
        ]

        daily, chain_tokens, addresses, address_tokens = (
            build_rollup_rows(transfers)
        )

        self.assertEqual(len(daily), 2)
        self.assertEqual(len(chain_tokens), 2)
        self.assertEqual(len(addresses), 2)
        self.assertEqual(len(address_tokens), 4)

        sender = next(
            row for row in addresses if row["address"] == "0xabc"
        )
        self.assertEqual(sender["sent_count"], 2)
        self.assertEqual(sender["activity_volume"], Decimal("20"))

    def test_preserves_solana_address_casing(self) -> None:
        transfers = [
            {
                "chain": "solana",
                "token_symbol": "USDC",
                "timestamp": datetime(2026, 8, 20, tzinfo=timezone.utc),
                "from_address": "SoLanaAddress",
                "to_address": "OtherAddress",
                "amount": Decimal("1"),
                "event_type": "transfer",
            },
        ]

        _, _, addresses, _ = build_rollup_rows(transfers)

        self.assertEqual(addresses[0]["address"], "SoLanaAddress")

    def test_preserves_tron_address_casing(self) -> None:
        transfers = [
            {
                "chain": "tron",
                "token_symbol": "USDT",
                "timestamp": datetime(2026, 8, 20, tzinfo=timezone.utc),
                "from_address": "TCaseSensitiveAddress",
                "to_address": "TAnotherAddress",
                "amount": Decimal("1"),
                "event_type": "transfer",
            },
        ]

        _, _, addresses, _ = build_rollup_rows(transfers)

        self.assertEqual(addresses[0]["address"], "TCaseSensitiveAddress")
