import asyncio
from aiohttp import ClientResponseError
from datetime import datetime
from datetime import timezone
from decimal import Decimal

from web3 import AsyncHTTPProvider
from web3 import AsyncWeb3
from web3 import Web3

from app.blockchain.chains import EvmChainConfig
from app.blockchain.erc20 import ERC20_TRANSFER_ABI
from app.blockchain.tokens import TokenConfig
from app.indexer.types import IndexedTransfer


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
RETRYABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}

def get_event_type(from_address: str, to_address: str) -> str:
    if from_address.lower() == ZERO_ADDRESS:
        return "mint"

    if to_address.lower() == ZERO_ADDRESS:
        return "burn"

    return "transfer"


def to_hex(value: bytes) -> str:
    hex_value = value.hex()

    if hex_value.startswith("0x"):
        return hex_value

    return f"0x{hex_value}"


class EvmIndexer:
    def __init__(
        self,
        chain: EvmChainConfig,
        token: TokenConfig,
    ) -> None:
        self.chain_config = chain
        self.chain = chain.name
        self.token = token

        self.w3 = AsyncWeb3(
            AsyncHTTPProvider(chain.rpc_url)
        )

        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.token.address),
            abi=ERC20_TRANSFER_ABI,
        )

    async def get_latest_block(self) -> int:
        return await self.w3.eth.block_number

    async def get_block_hash(self, block_number: int) -> str:
        block = await self.w3.eth.get_block(block_number)

        return to_hex(block["hash"])

    async def get_block_with_retry(
        self,
        block_number: int,
        semaphore: asyncio.Semaphore,
    ) -> dict:
        async with semaphore:
            delay = 1

            for attempt in range(5):
                try:
                    return await self.w3.eth.get_block(block_number)
                except ClientResponseError as exc:
                    if exc.status not in RETRYABLE_HTTP_STATUSES or attempt == 4:
                        raise

                    await asyncio.sleep(delay)
                    delay *= 2

            raise RuntimeError(
                f"Failed to fetch block {block_number}"
            )

    async def get_transfers(
        self,
        from_block: int,
        to_block: int,
    ) -> list[IndexedTransfer]:
        if from_block > to_block:
            raise ValueError("from_block must be <= to_block")

        logs = await self.get_logs_with_retry(
            from_block=from_block,
            to_block=to_block,
        )

        block_numbers = sorted(
            {log["blockNumber"] for log in logs}
        )

        semaphore = asyncio.Semaphore(3)

        blocks = await asyncio.gather(
            *(
                self.get_block_with_retry(number, semaphore)
                for number in block_numbers
            )
        )

        timestamps = {
            block["number"]: datetime.fromtimestamp(
                block["timestamp"],
                tz=timezone.utc,
            )
            for block in blocks
        }

        divisor = Decimal(10) ** self.token.decimals
        transfers: list[IndexedTransfer] = []

        for log in logs:
            amount_raw = Decimal(log["args"]["value"])

            transfers.append(
                IndexedTransfer(
                    chain=self.chain,
                    token_symbol=self.token.symbol,
                    token_address=self.token.address,
                    transaction_hash=to_hex(log["transactionHash"]),
                    log_index=log["logIndex"],
                    block_number=log["blockNumber"],
                    block_hash=to_hex(log["blockHash"]),
                    timestamp=timestamps[log["blockNumber"]],
                    from_address=log["args"]["from"],
                    to_address=log["args"]["to"],
                    amount_raw=amount_raw,
                    amount=amount_raw / divisor,
                    event_type=get_event_type(
                        log["args"]["from"],
                        log["args"]["to"],
                    ),
                )
            )

        return transfers
    
    async def get_logs_with_retry(
        self,
        from_block: int,
        to_block: int,
    ) -> list:
        delay = 1

        for attempt in range(5):
            try:
                return await self.contract.events.Transfer().get_logs(
                    from_block=from_block,
                    to_block=to_block,
                )
            except ClientResponseError as exc:
                if exc.status not in RETRYABLE_HTTP_STATUSES or attempt == 4:
                    raise

                await asyncio.sleep(delay)
                delay *= 2

        raise RuntimeError(
            f"Failed to fetch logs for blocks {from_block}-{to_block}"
        )