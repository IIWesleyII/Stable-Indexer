from datetime import datetime
from datetime import timezone
from decimal import Decimal
from unittest import IsolatedAsyncioTestCase
from unittest import TestCase

from app.blockchain.chains import TronChainConfig
from app.blockchain.tron import TronIndexer
from app.blockchain.tron import tron_hex_to_base58


class TronAddressTests(TestCase):
    def test_converts_tether_contract_to_base58(self) -> None:
        self.assertEqual(
            tron_hex_to_base58(
                "a614f803b6fd780986a42c78ec9c7f77e6ded13c"
            ),
            "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
        )


class TronIndexerTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.indexer = TronIndexer(
            chain=TronChainConfig(
                name="tron",
                api_url="https://example.invalid",
                api_key="test-key",
            )
        )

    async def asyncTearDown(self) -> None:
        await self.indexer.close()

    async def test_get_transfers_parses_confirmed_usdt_events(self) -> None:
        self.indexer.get_block_timestamp = self._get_block_timestamp
        self.indexer._get_events = self._get_events
        self.indexer._get_block_hashes = self._get_block_hashes

        transfers = await self.indexer.get_transfers(10, 11)

        self.assertEqual(len(transfers), 1)
        transfer = transfers[0]
        self.assertEqual(transfer.chain, "tron")
        self.assertEqual(transfer.token_symbol, "USDT")
        self.assertEqual(
            transfer.from_address,
            "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
        )
        self.assertEqual(
            transfer.to_address,
            "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
        )
        self.assertEqual(transfer.amount_raw, Decimal("2600000000"))
        self.assertEqual(transfer.amount, Decimal("2600"))
        self.assertEqual(transfer.block_hash, "block-10")
        self.assertEqual(
            transfer.timestamp,
            datetime.fromtimestamp(10, tz=timezone.utc),
        )

    async def _get_block_timestamp(self, block_number: int) -> int:
        return block_number

    async def _get_events(
        self,
        min_timestamp: int,
        max_timestamp: int,
    ) -> list[dict]:
        self.assertEqual((min_timestamp, max_timestamp), (10000, 11000))
        return [
            {
                "block_number": 10,
                "block_timestamp": 10000,
                "event_index": 2,
                "transaction_id": "transaction-id",
                "result": {
                    "from": "a614f803b6fd780986a42c78ec9c7f77e6ded13c",
                    "to": "a614f803b6fd780986a42c78ec9c7f77e6ded13c",
                    "value": "2600000000",
                },
            },
            {
                "block_number": 12,
                "block_timestamp": 12000,
                "event_index": 0,
                "transaction_id": "outside-range",
                "result": {
                    "from": "a614f803b6fd780986a42c78ec9c7f77e6ded13c",
                    "to": "a614f803b6fd780986a42c78ec9c7f77e6ded13c",
                    "value": "1",
                },
            },
        ]

    async def _get_block_hashes(
        self,
        from_block: int,
        to_block: int,
    ) -> dict[int, str]:
        self.assertEqual((from_block, to_block), (10, 11))
        return {10: "block-10", 11: "block-11"}
