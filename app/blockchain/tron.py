import asyncio
import hashlib
from datetime import datetime
from datetime import timezone
from decimal import Decimal
from typing import Any

from aiohttp import ClientConnectionError
from aiohttp import ClientResponseError
from aiohttp import ClientSession
from aiohttp import ClientTimeout

from app.blockchain.chains import TRON_MAINNET
from app.blockchain.chains import TronChainConfig
from app.blockchain.tokens import TRON_USDT
from app.blockchain.tokens import TokenConfig
from app.indexer.types import IndexedTransfer


BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
RETRYABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}
TRON_ADDRESS_PREFIX = b"\x41"
TRON_ZERO_ADDRESS = "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb"


class TronRpcError(Exception):
    pass


def tron_hex_to_base58(address: str) -> str:
    value = address.removeprefix("0x")

    if len(value) == 40:
        payload = TRON_ADDRESS_PREFIX + bytes.fromhex(value)
    elif len(value) == 42 and value.startswith("41"):
        payload = bytes.fromhex(value)
    else:
        raise ValueError(f"Invalid Tron hex address: {address}")

    checksum = hashlib.sha256(
        hashlib.sha256(payload).digest()
    ).digest()[:4]
    encoded = payload + checksum
    number = int.from_bytes(encoded, byteorder="big")
    characters: list[str] = []

    while number:
        number, remainder = divmod(number, 58)
        characters.append(BASE58_ALPHABET[remainder])

    leading_zeroes = len(encoded) - len(encoded.lstrip(b"\0"))

    return "1" * leading_zeroes + "".join(reversed(characters))


def get_event_type(from_address: str, to_address: str) -> str:
    if from_address == TRON_ZERO_ADDRESS:
        return "mint"

    if to_address == TRON_ZERO_ADDRESS:
        return "burn"

    return "transfer"


class TronIndexer:
    def __init__(
        self,
        chain: TronChainConfig = TRON_MAINNET,
        token: TokenConfig = TRON_USDT,
    ) -> None:
        if not chain.api_key:
            raise RuntimeError(
                "TRONGRID_API_KEY is required for Tron indexing"
            )

        self.chain_config = chain
        self.chain = chain.name
        self.token = token
        self.session: ClientSession | None = None
        self.blocks: dict[int, dict[str, Any]] = {}

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()

    async def get_latest_block(self) -> int:
        block = await self._post("/walletsolidity/getnowblock", {})
        return self._block_number(block)

    async def get_block_hash(self, block_number: int) -> str:
        return (await self._get_block(block_number))["blockID"]

    async def get_block_timestamp(self, block_number: int) -> int:
        block = await self._get_block(block_number)
        return self._block_timestamp_ms(block) // 1000

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
            middle_timestamp = await self.get_block_timestamp(middle)

            if middle_timestamp < timestamp:
                low = middle + 1
            else:
                high = middle

        return low

    async def get_transfers(
        self,
        from_block: int,
        to_block: int,
    ) -> list[IndexedTransfer]:
        if from_block > to_block:
            raise ValueError("from_block must be <= to_block")

        start_timestamp = await self.get_block_timestamp(from_block)
        end_timestamp = await self.get_block_timestamp(to_block)
        events = await self._get_events(
            start_timestamp * 1000,
            end_timestamp * 1000,
        )
        events = [
            event
            for event in events
            if from_block <= int(event["block_number"]) <= to_block
        ]

        if not events:
            return []

        block_hashes = await self._get_block_hashes(
            from_block,
            to_block,
        )
        transfers = [
            self._parse_event(event, block_hashes)
            for event in events
        ]
        transfers.sort(
            key=lambda transfer: (
                transfer.block_number,
                transfer.transaction_hash,
                transfer.log_index,
            )
        )

        return transfers

    async def _get_events(
        self,
        min_timestamp: int,
        max_timestamp: int,
    ) -> list[dict[str, Any]]:
        params: dict[str, str | int] = {
            "event_name": "Transfer",
            "only_confirmed": "true",
            "min_timestamp": min_timestamp,
            "max_timestamp": max_timestamp,
            "order_by": "block_timestamp,asc",
            "limit": 200,
        }
        events: list[dict[str, Any]] = []
        seen_fingerprints: set[str] = set()

        while True:
            payload = await self._get(
                f"/v1/contracts/{self.token.address}/events",
                params,
            )
            events.extend(payload.get("data", []))
            fingerprint = payload.get("meta", {}).get("fingerprint")

            if not fingerprint:
                return events

            if fingerprint in seen_fingerprints:
                raise TronRpcError("TronGrid returned a repeated fingerprint")

            seen_fingerprints.add(fingerprint)
            params["fingerprint"] = fingerprint

    async def _get_block(self, block_number: int) -> dict[str, Any]:
        if block_number not in self.blocks:
            block = await self._post(
                "/walletsolidity/getblockbynum",
                {"num": block_number},
            )
            self.blocks[block_number] = block

        return self.blocks[block_number]

    async def _get_block_hashes(
        self,
        from_block: int,
        to_block: int,
    ) -> dict[int, str]:
        payload = await self._post(
            "/walletsolidity/getblockbylimitnext",
            {
                "startNum": from_block,
                "endNum": to_block + 1,
            },
        )
        blocks = payload.get("block", [])
        block_hashes: dict[int, str] = {}

        for block in blocks:
            block_number = self._block_number(block)
            self.blocks[block_number] = block
            block_hashes[block_number] = block["blockID"]

        missing_blocks = {
            block_number
            for block_number in range(from_block, to_block + 1)
            if block_number not in block_hashes
        }

        if missing_blocks:
            missing = ", ".join(str(block) for block in sorted(missing_blocks))
            raise TronRpcError(f"TronGrid omitted blocks: {missing}")

        return block_hashes

    def _parse_event(
        self,
        event: dict[str, Any],
        block_hashes: dict[int, str],
    ) -> IndexedTransfer:
        result = event["result"]
        from_address = tron_hex_to_base58(result["from"])
        to_address = tron_hex_to_base58(result["to"])
        amount_raw = Decimal(result["value"])
        block_number = int(event["block_number"])

        return IndexedTransfer(
            chain=self.chain,
            token_symbol=self.token.symbol,
            token_address=self.token.address,
            transaction_hash=event["transaction_id"],
            log_index=int(event["event_index"]),
            block_number=block_number,
            block_hash=block_hashes[block_number],
            timestamp=datetime.fromtimestamp(
                int(event["block_timestamp"]) / 1000,
                tz=timezone.utc,
            ),
            from_address=from_address,
            to_address=to_address,
            amount_raw=amount_raw,
            amount=amount_raw / (Decimal(10) ** self.token.decimals),
            event_type=get_event_type(from_address, to_address),
        )

    async def _get(
        self,
        path: str,
        params: dict[str, str | int],
    ) -> dict[str, Any]:
        session = await self._get_session()

        return await self._request(
            "get",
            path,
            params=params,
            json=None,
            session=session,
        )

    async def _post(
        self,
        path: str,
        body: dict[str, int],
    ) -> dict[str, Any]:
        session = await self._get_session()

        return await self._request(
            "post",
            path,
            params=None,
            json=body,
            session=session,
        )

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str | int] | None,
        json: dict[str, int] | None,
        session: ClientSession,
    ) -> dict[str, Any]:
        delay = 1

        for attempt in range(5):
            try:
                async with session.request(
                    method,
                    f"{self.chain_config.api_url}{path}",
                    params=params,
                    json=json,
                ) as response:
                    response.raise_for_status()
                    payload = await response.json()
            except (
                ClientConnectionError,
                ClientResponseError,
                asyncio.TimeoutError,
            ) as exc:
                status = getattr(exc, "status", None)

                if (
                    status is not None
                    and status not in RETRYABLE_HTTP_STATUSES
                ) or attempt == 4:
                    message = (
                        f"{self.chain} TronGrid request failed"
                        if status is None
                        else f"{self.chain} TronGrid request failed with HTTP {status}"
                    )
                    raise TronRpcError(message) from None

                await asyncio.sleep(delay)
                delay *= 2
                continue

            if "Error" in payload:
                raise TronRpcError(payload["Error"])

            return payload

        raise RuntimeError(f"Failed TronGrid request: {path}")

    async def _get_session(self) -> ClientSession:
        if self.session is None or self.session.closed:
            self.session = ClientSession(
                headers={
                    "TRON-PRO-API-KEY": self.chain_config.api_key,
                },
                timeout=ClientTimeout(total=60),
            )

        return self.session

    @staticmethod
    def _block_number(block: dict[str, Any]) -> int:
        return int(block["block_header"]["raw_data"]["number"])

    @staticmethod
    def _block_timestamp_ms(block: dict[str, Any]) -> int:
        return int(block["block_header"]["raw_data"]["timestamp"])
