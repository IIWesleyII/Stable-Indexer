import asyncio
from datetime import datetime
from datetime import timezone
from decimal import Decimal
from typing import Any

from aiohttp import ClientResponseError
from aiohttp import ClientSession
from aiohttp import ClientTimeout

from app.blockchain.chains import SOLANA_MAINNET
from app.blockchain.chains import SolanaChainConfig
from app.blockchain.tokens import SOLANA_USDC
from app.blockchain.tokens import SOLANA_USDT
from app.blockchain.tokens import TokenConfig
from app.indexer.types import IndexedTransfer


RETRYABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}
BLOCK_CONCURRENCY = 3


class SolanaRpcError(Exception):
    pass


class SolanaSlotUnavailableError(SolanaRpcError):
    pass


class SolanaIndexer:
    def __init__(
        self,
        chain: SolanaChainConfig = SOLANA_MAINNET,
        tokens: tuple[TokenConfig, ...] = (
            SOLANA_USDC,
            SOLANA_USDT,
        ),
    ) -> None:
        if not chain.rpc_url:
            raise RuntimeError(
                "SOLANA_RPC_URL is required for Solana indexing"
            )

        self.chain_config = chain
        self.chain = chain.name
        self.tokens = tokens
        self.tokens_by_address = {
            token.address: token
            for token in tokens
        }
        # Retained for code that uses the primary configured token.
        self.token = tokens[0]
        self.session: ClientSession | None = None
        self.blocks: dict[int, dict[str, Any] | None] = {}

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()

    async def get_latest_block(self) -> int:
        return await self._rpc(
            "getSlot",
            [{"commitment": "finalized"}],
        )

    async def get_block_hash(self, block_number: int) -> str:
        block = await self._get_block(block_number)

        if block is None:
            return f"skipped:{block_number}"

        return block["blockhash"]

    async def get_transfers(
        self,
        from_block: int,
        to_block: int,
    ) -> list[IndexedTransfer]:
        if from_block > to_block:
            raise ValueError("from_block must be <= to_block")

        semaphore = asyncio.Semaphore(BLOCK_CONCURRENCY)

        blocks = await asyncio.gather(
            *(
                self._get_block_with_semaphore(
                    slot,
                    semaphore,
                )
                for slot in range(from_block, to_block + 1)
            )
        )

        transfers: list[IndexedTransfer] = []

        for slot, block in zip(
            range(from_block, to_block + 1),
            blocks,
            strict=True,
        ):
            if block is not None:
                transfers.extend(
                    self._parse_block(slot, block)
                )

        return transfers

    async def _get_block_with_semaphore(
        self,
        slot: int,
        semaphore: asyncio.Semaphore,
    ) -> dict[str, Any] | None:
        async with semaphore:
            return await self._get_block(slot)

    async def _get_block(
        self,
        slot: int,
    ) -> dict[str, Any] | None:
        if slot not in self.blocks:
            try:
                self.blocks[slot] = await self._rpc(
                    "getBlock",
                    [
                        slot,
                        {
                            "commitment": "finalized",
                            "encoding": "jsonParsed",
                            "maxSupportedTransactionVersion": 0,
                            "rewards": False,
                            "transactionDetails": "full",
                        },
                    ],
                )
            except SolanaSlotUnavailableError:
                self.blocks[slot] = None

        return self.blocks[slot]

    async def _rpc(
        self,
        method: str,
        params: list[Any],
    ) -> Any:
        session = await self._get_session()
        delay = 1

        for attempt in range(5):
            try:
                async with session.post(
                    self.chain_config.rpc_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": method,
                        "params": params,
                    },
                ) as response:
                    response.raise_for_status()
                    payload = await response.json()
            except ClientResponseError as exc:
                if (
                    exc.status not in RETRYABLE_HTTP_STATUSES
                    or attempt == 4
                ):
                    raise SolanaRpcError(
                        f"{method} failed with HTTP {exc.status}"
                    ) from None

                await asyncio.sleep(delay)
                delay *= 2
                continue

            if "error" in payload:
                error = payload["error"]
                message = error["message"]

                if (
                    method == "getBlock"
                    and (
                        error.get("code") == -32007
                        or "was skipped, or missing in long-term storage"
                        in message
                    )
                ):
                    raise SolanaSlotUnavailableError(
                        message
                    )

                raise SolanaRpcError(
                    f"{method} failed: {message}"
                )

            return payload["result"]

        raise RuntimeError(f"Failed Solana RPC request: {method}")

    async def _get_session(self) -> ClientSession:
        if self.session is None or self.session.closed:
            self.session = ClientSession(
                timeout=ClientTimeout(total=30),
            )

        return self.session

    def _parse_block(
        self,
        slot: int,
        block: dict[str, Any],
    ) -> list[IndexedTransfer]:
        block_time = block.get("blockTime")

        if block_time is None:
            return []

        timestamp = datetime.fromtimestamp(
            block_time,
            tz=timezone.utc,
        )
        transfers: list[IndexedTransfer] = []

        for transaction in block.get("transactions", []):
            if transaction.get("meta", {}).get("err") is not None:
                continue

            transfers.extend(
                self._parse_transaction(
                    slot,
                    block["blockhash"],
                    timestamp,
                    transaction,
                )
            )

        return transfers

    def _parse_transaction(
        self,
        slot: int,
        block_hash: str,
        timestamp: datetime,
        transaction: dict[str, Any],
    ) -> list[IndexedTransfer]:
        message = transaction["transaction"]["message"]
        signature = transaction["transaction"]["signatures"][0]
        token_account_owners, token_accounts = (
            self._get_token_account_metadata(
                message,
                transaction.get("meta", {}),
            )
        )
        transfers: list[IndexedTransfer] = []

        for log_index, instruction in enumerate(
            self._iter_instructions(
                message,
                transaction.get("meta", {}),
            )
        ):
            info = self._get_transfer_info(
                instruction,
                token_account_owners,
                token_accounts,
            )

            if info is None:
                continue

            source, destination, amount_raw, token = info
            divisor = Decimal(10) ** token.decimals

            transfers.append(
                IndexedTransfer(
                    chain=self.chain,
                    token_symbol=token.symbol,
                    token_address=token.address,
                    transaction_hash=signature,
                    log_index=log_index,
                    block_number=slot,
                    block_hash=block_hash,
                    timestamp=timestamp,
                    from_address=token_account_owners.get(
                        source,
                        source,
                    ),
                    to_address=token_account_owners.get(
                        destination,
                        destination,
                    ),
                    amount_raw=amount_raw,
                    amount=amount_raw / divisor,
                    event_type="transfer",
                )
            )

        return transfers

    def _get_token_account_metadata(
        self,
        message: dict[str, Any],
        meta: dict[str, Any],
    ) -> tuple[dict[str, str], dict[str, TokenConfig]]:
        account_keys = message.get("accountKeys", [])
        owners: dict[str, str] = {}
        tokens: dict[str, TokenConfig] = {}

        for balance in (
            meta.get("preTokenBalances", [])
            + meta.get("postTokenBalances", [])
        ):
            token = self.tokens_by_address.get(balance.get("mint"))

            if token is None:
                continue

            account_index = balance["accountIndex"]

            if account_index >= len(account_keys):
                continue

            account = account_keys[account_index]
            public_key = (
                account["pubkey"]
                if isinstance(account, dict)
                else account
            )
            owner = balance.get("owner")

            tokens[public_key] = token

            if owner:
                owners[public_key] = owner

        return owners, tokens

    def _iter_instructions(
        self,
        message: dict[str, Any],
        meta: dict[str, Any],
    ):
        inner_by_index = {
            item["index"]: item.get("instructions", [])
            for item in meta.get("innerInstructions", [])
        }

        for index, instruction in enumerate(
            message.get("instructions", [])
        ):
            yield instruction
            yield from inner_by_index.get(index, [])

    def _get_transfer_info(
        self,
        instruction: dict[str, Any],
        token_account_owners: dict[str, str],
        token_accounts: dict[str, TokenConfig],
    ) -> tuple[str, str, Decimal, TokenConfig] | None:
        parsed = instruction.get("parsed")

        if not isinstance(parsed, dict):
            return None

        if parsed.get("type") not in {"transfer", "transferChecked"}:
            return None

        info = parsed.get("info", {})
        source = info.get("source")
        destination = info.get("destination")

        if not source or not destination:
            return None

        token = self.tokens_by_address.get(info.get("mint"))

        if token is None:
            token = token_accounts.get(source)

        if token is None:
            token = token_accounts.get(destination)

        if token is None:
            return None

        amount = info.get("amount")

        if amount is None:
            return None

        return source, destination, Decimal(amount), token
