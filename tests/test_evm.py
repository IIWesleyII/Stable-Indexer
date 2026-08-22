from datetime import datetime
from datetime import timezone
from unittest import IsolatedAsyncioTestCase

from app.blockchain.chains import EvmChainConfig
from app.blockchain.evm import EvmIndexer
from app.blockchain.tokens import TokenConfig


class FakeEvmIndexer(EvmIndexer):
    def __init__(self, timestamps: list[int]) -> None:
        self.timestamps = timestamps

    async def get_latest_block(self) -> int:
        return len(self.timestamps) - 1

    async def get_block_timestamp(self, block_number: int) -> int:
        return self.timestamps[block_number]


class EvmTimestampSearchTests(IsolatedAsyncioTestCase):
    async def test_finds_first_block_at_or_after_timestamp(self) -> None:
        indexer = FakeEvmIndexer([100, 110, 120, 130, 140])

        block = await indexer.get_block_at_or_after_timestamp(125)

        self.assertEqual(block, 3)

    async def test_uses_provided_latest_block(self) -> None:
        indexer = FakeEvmIndexer([100, 110, 120, 130, 140])

        block = await indexer.get_block_at_or_after_timestamp(
            115,
            latest_block=3,
        )

        self.assertEqual(block, 2)


class EvmMultiTokenTests(IsolatedAsyncioTestCase):
    async def test_preserves_each_token_metadata(self) -> None:
        usdc = TokenConfig(
            "USDC",
            "0x0000000000000000000000000000000000000001",
            6,
        )
        usdt = TokenConfig(
            "USDT",
            "0x0000000000000000000000000000000000000002",
            6,
        )
        indexer = FakeMultiTokenEvmIndexer((usdc, usdt))

        transfers = await indexer.get_transfers(100, 100)

        self.assertEqual(
            [transfer.token_symbol for transfer in transfers],
            ["USDC", "USDT"],
        )
        self.assertEqual(
            [str(transfer.amount) for transfer in transfers],
            ["1.5", "2.5"],
        )


class FakeMultiTokenEvmIndexer(EvmIndexer):
    def __init__(self, tokens: tuple[TokenConfig, ...]) -> None:
        self.chain_config = EvmChainConfig(
            name="ethereum",
            rpc_url="https://example.invalid",
            chain_id=1,
        )
        self.chain = self.chain_config.name
        self.tokens = tokens
        self.token = tokens[0]

    async def get_logs_with_retry(
        self,
        token: TokenConfig,
        from_block: int,
        to_block: int,
    ) -> list:
        amount = 1_500_000 if token.symbol == "USDC" else 2_500_000

        return [
            {
                "args": {
                    "from": "0x0000000000000000000000000000000000000003",
                    "to": "0x0000000000000000000000000000000000000004",
                    "value": amount,
                },
                "blockHash": b"\x02",
                "blockNumber": 100,
                "logIndex": 0 if token.symbol == "USDC" else 1,
                "transactionHash": b"\x01",
            }
        ]

    async def get_block_with_retry(
        self,
        block_number: int,
        semaphore,
    ) -> dict:
        return {
            "number": block_number,
            "timestamp": int(
                datetime(2026, 8, 18, tzinfo=timezone.utc).timestamp()
            ),
        }
