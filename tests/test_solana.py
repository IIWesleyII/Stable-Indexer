from datetime import datetime
from datetime import timezone
import unittest

from app.blockchain.chains import SolanaChainConfig
from app.blockchain.solana import SolanaIndexer
from app.blockchain.solana import SolanaSlotUnavailableError
from app.blockchain.tokens import SOLANA_USDT


class SolanaIndexerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.indexer = SolanaIndexer(
            chain=SolanaChainConfig(
                name="solana",
                rpc_url="https://example.invalid",
            )
        )
        self.source_token_account = "SourceTokenAccount"
        self.destination_token_account = "DestinationTokenAccount"

    def test_parses_transfer_checked_to_wallet_addresses(self) -> None:
        transaction = self._transaction(
            instructions=[
                {
                    "parsed": {
                        "type": "transferChecked",
                        "info": {
                            "amount": "1234000",
                            "destination": self.destination_token_account,
                            "mint": self.indexer.token.address,
                            "source": self.source_token_account,
                        },
                    },
                },
            ],
        )

        transfers = self._parse(transaction)

        self.assertEqual(len(transfers), 1)
        self.assertEqual(transfers[0].from_address, "SourceWallet")
        self.assertEqual(transfers[0].to_address, "DestinationWallet")
        self.assertEqual(str(transfers[0].amount), "1.234")

    def test_parses_inner_transfer_using_token_balances(self) -> None:
        transaction = self._transaction(
            instructions=[{"program": "system"}],
            inner_instructions=[
                {
                    "index": 0,
                    "instructions": [
                        {
                            "parsed": {
                                "type": "transfer",
                                "info": {
                                    "amount": "500000",
                                    "destination": self.destination_token_account,
                                    "source": self.source_token_account,
                                },
                            },
                        },
                    ],
                },
            ],
        )

        transfers = self._parse(transaction)

        self.assertEqual(len(transfers), 1)
        self.assertEqual(transfers[0].log_index, 1)
        self.assertEqual(str(transfers[0].amount), "0.5")

    def test_parses_usdt_transfer_checked(self) -> None:
        transaction = self._transaction(
            instructions=[
                {
                    "parsed": {
                        "type": "transferChecked",
                        "info": {
                            "amount": "2000000",
                            "destination": self.destination_token_account,
                            "mint": SOLANA_USDT.address,
                            "source": self.source_token_account,
                        },
                    },
                },
            ],
            mint=SOLANA_USDT.address,
        )

        transfers = self._parse(transaction)

        self.assertEqual(len(transfers), 1)
        self.assertEqual(transfers[0].token_symbol, "USDT")
        self.assertEqual(str(transfers[0].amount), "2")

    def _parse(self, transaction: dict):
        return self.indexer._parse_transaction(
            slot=123,
            block_hash="BlockHash",
            timestamp=datetime.now(timezone.utc),
            transaction=transaction,
        )

    def _transaction(
        self,
        instructions: list[dict],
        inner_instructions: list[dict] | None = None,
        mint: str | None = None,
    ) -> dict:
        return {
            "transaction": {
                "signatures": ["TransactionSignature"],
                "message": {
                    "accountKeys": [
                        {"pubkey": self.source_token_account},
                        {"pubkey": self.destination_token_account},
                    ],
                    "instructions": instructions,
                },
            },
            "meta": {
                "err": None,
                "innerInstructions": inner_instructions or [],
                "postTokenBalances": [
                    {
                        "accountIndex": 1,
                        "mint": mint or self.indexer.token.address,
                        "owner": "DestinationWallet",
                    },
                ],
                "preTokenBalances": [
                    {
                        "accountIndex": 0,
                        "mint": mint or self.indexer.token.address,
                        "owner": "SourceWallet",
                    },
                ],
            },
        }


class SolanaSkippedSlotTests(unittest.IsolatedAsyncioTestCase):
    async def test_skipped_slot_is_treated_as_empty_block(self) -> None:
        indexer = SolanaIndexer(
            chain=SolanaChainConfig(
                name="solana",
                rpc_url="https://example.invalid",
            )
        )

        async def skipped_slot(method: str, params: list):
            raise SolanaSlotUnavailableError("slot was skipped")

        indexer._rpc = skipped_slot

        block = await indexer._get_block(123)

        self.assertIsNone(block)
        self.assertIn(123, indexer.blocks)


if __name__ == "__main__":
    unittest.main()
