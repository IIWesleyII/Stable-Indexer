import asyncio
import logging
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


class EvmRpcError(Exception):
    pass


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
        token: TokenConfig | None = None,
        tokens: tuple[TokenConfig, ...] | None = None,
    ) -> None:
        if token is not None and tokens is not None:
            raise ValueError("Provide either token or tokens, not both")

        if tokens is None:
            if token is None:
                raise ValueError("At least one token is required")

            tokens = (token,)

        self.chain_config = chain
        self.chain = chain.name
        self.tokens = tokens
        # Retained for the single-token historical importer.
        self.token = tokens[0]

        self.w3 = AsyncWeb3(
            AsyncHTTPProvider(chain.rpc_url)
        )
        self.w3.provider.logger.setLevel(logging.WARNING)

        self.contracts = {
            token.address.lower(): self.w3.eth.contract(
                address=Web3.to_checksum_address(token.address),
                abi=ERC20_TRANSFER_ABI,
            )
            for token in self.tokens
        }

    async def close(self) -> None:
        await self.w3.provider.disconnect()

    async def get_latest_block(self) -> int:
        try:
            return await self.w3.eth.block_number
        except ClientResponseError as exc:
            raise EvmRpcError(
                f"{self.chain} RPC request failed with HTTP {exc.status}"
            ) from None

    async def get_block_hash(self, block_number: int) -> str:
        block = await self.w3.eth.get_block(block_number)

        return to_hex(block["hash"])

    async def get_block_timestamp(
        self,
        block_number: int,
    ) -> int:
        block = await self.w3.eth.get_block(block_number)

        return block["timestamp"]

    async def get_block_at_or_after_timestamp(
        self,
        timestamp: int,
        latest_block: int | None = None,
    ) -> int:
        if latest_block is None:
            latest_block = await self.get_latest_block()

        low = 0
        high = latest_block

        while low < high:
            middle = (low + high) // 2
            middle_timestamp = await self.get_block_timestamp(
                middle
            )

            if middle_timestamp < timestamp:
                low = middle + 1
            else:
                high = middle

        return low

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
                    if (
                        exc.status not in RETRYABLE_HTTP_STATUSES
                        or attempt == 4
                    ):
                        raise EvmRpcError(
                            f"{self.chain} RPC request failed "
                            f"with HTTP {exc.status}"
                        ) from None

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

        token_logs = await asyncio.gather(
            *(
                self.get_logs_with_retry(
                    token=token,
                    from_block=from_block,
                    to_block=to_block,
                )
                for token in self.tokens
            )
        )

        logs = [
            (token, log)
            for token, entries in zip(
                self.tokens,
                token_logs,
                strict=True,
            )
            for log in entries
        ]

        block_numbers = sorted(
            {log["blockNumber"] for _, log in logs}
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

        transfers: list[IndexedTransfer] = []

        for token, log in logs:
            amount_raw = Decimal(log["args"]["value"])
            divisor = Decimal(10) ** token.decimals

            transfers.append(
                IndexedTransfer(
                    chain=self.chain,
                    token_symbol=token.symbol,
                    token_address=token.address,
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
        token: TokenConfig,
        from_block: int,
        to_block: int,
    ) -> list:
        delay = 1

        for attempt in range(5):
            try:
                contract = self.contracts[token.address.lower()]

                return await contract.events.Transfer().get_logs(
                    from_block=from_block,
                    to_block=to_block,
                )
            except ClientResponseError as exc:
                if exc.status == 400 and from_block < to_block:
                    midpoint = (from_block + to_block) // 2

                    first_half = await self.get_logs_with_retry(
                        token=token,
                        from_block=from_block,
                        to_block=midpoint,
                    )
                    second_half = await self.get_logs_with_retry(
                        token=token,
                        from_block=midpoint + 1,
                        to_block=to_block,
                    )

                    return first_half + second_half

                if exc.status not in RETRYABLE_HTTP_STATUSES or attempt == 4:
                    raise EvmRpcError(
                        f"{self.chain} RPC request failed "
                        f"with HTTP {exc.status}"
                    ) from None

                await asyncio.sleep(delay)
                delay *= 2

        raise RuntimeError(
            f"Failed to fetch logs for blocks {from_block}-{to_block}"
        )
