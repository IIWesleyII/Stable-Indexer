from unittest import TestCase

from app.blockchain.tokens import BASE_USDC
from app.indexer.alchemy import AlchemyImportError
from app.indexer.alchemy import AlchemyTransferClient


class AlchemyTransferClientTests(TestCase):
    def setUp(self) -> None:
        self.client = AlchemyTransferClient(
            chain="base",
            rpc_url="https://base-mainnet.g.alchemy.com/v2/test-key",
            token=BASE_USDC,
        )

    def test_parses_erc20_transfer(self) -> None:
        transfer = self.client._parse_transfer(
            {
                "uniqueId": "0xtransaction:12",
                "hash": "0xtransaction",
                "blockNum": "0x2ab9e5",
                "from": "0x1111111111111111111111111111111111111111",
                "to": "0x2222222222222222222222222222222222222222",
                "rawContract": {"value": "0x12d687"},
                "metadata": {
                    "blockTimestamp": "2023-08-09T00:00:00.000Z",
                },
            }
        )

        self.assertEqual(transfer.chain, "base")
        self.assertEqual(transfer.log_index, 12)
        self.assertEqual(transfer.block_number, 2800101)
        self.assertEqual(str(transfer.amount_raw), "1234567")
        self.assertEqual(str(transfer.amount), "1.234567")
        self.assertEqual(transfer.event_type, "transfer")
        self.assertEqual(transfer.block_hash, "provider:alchemy")

    def test_parses_mint_transfer(self) -> None:
        transfer = self.client._parse_transfer(
            {
                "uniqueId": "0xtransaction:0x7",
                "hash": "0xtransaction",
                "blockNum": "0x1",
                "from": "0x0000000000000000000000000000000000000000",
                "to": "0x2222222222222222222222222222222222222222",
                "rawContract": {"value": "0x1"},
                "metadata": {
                    "blockTimestamp": "2023-08-09T00:00:00Z",
                },
            }
        )

        self.assertEqual(transfer.log_index, 7)
        self.assertEqual(transfer.event_type, "mint")

    def test_rejects_non_alchemy_endpoint(self) -> None:
        with self.assertRaises(ValueError):
            AlchemyTransferClient(
                chain="base",
                rpc_url="https://mainnet.base.org",
                token=BASE_USDC,
            )

    def test_rejects_unique_id_without_log_index(self) -> None:
        with self.assertRaises(AlchemyImportError):
            self.client._parse_log_index("0xtransaction")
