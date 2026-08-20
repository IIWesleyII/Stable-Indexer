import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from datetime import timezone
from decimal import Decimal
from typing import Any

from aiohttp import ClientResponseError
from aiohttp import ClientSession
from aiohttp import ClientTimeout

from app.blockchain.evm import get_event_type
from app.blockchain.tokens import TokenConfig
from app.indexer.types import IndexedTransfer


RETRYABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}


class AlchemyImportError(Exception):
    pass


class AlchemyTransferClient:
    def __init__(
        self,
        chain: str,
        rpc_url: str,
        token: TokenConfig,
    ) -> None:
        if "alchemy.com" not in rpc_url.lower():
            raise ValueError(
                f"{chain} requires an Alchemy RPC URL for this importer"
            )

        self.chain = chain
        self.rpc_url = rpc_url
        self.token = token
        self.session: ClientSession | None = None

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()

    async def iter_transfers(
        self,
        from_block: int,
        to_block: int,
        max_pages: int | None = None,
    ) -> AsyncIterator[list[IndexedTransfer]]:
        page_key: str | None = None
        page_count = 0

        while max_pages is None or page_count < max_pages:
            response = await self._request(
                "alchemy_getAssetTransfers",
                [
                    {
                        "fromBlock": hex(from_block),
                        "toBlock": hex(to_block),
                        "contractAddresses": [self.token.address],
                        "category": ["erc20"],
                        "excludeZeroValue": False,
                        "withMetadata": True,
                        "maxCount": "0x3e8",
                        **(
                            {"pageKey": page_key}
                            if page_key is not None
                            else {}
                        ),
                    }
                ],
            )
            page_count += 1
            transfers = response.get("transfers", [])

            yield [
                self._parse_transfer(transfer)
                for transfer in transfers
            ]

            page_key = response.get("pageKey")
            if not page_key:
                return

    async def _request(
        self,
        method: str,
        params: list[Any],
    ) -> dict[str, Any]:
        session = await self._get_session()
        delay = 1

        for attempt in range(5):
            try:
                async with session.post(
                    self.rpc_url,
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
                    raise AlchemyImportError(
                        f"{self.chain} Alchemy request failed with HTTP "
                        f"{exc.status}"
                    ) from None

                await asyncio.sleep(delay)
                delay *= 2
                continue

            if "error" in payload:
                error = payload["error"]
                raise AlchemyImportError(
                    f"{self.chain} Alchemy request failed: "
                    f"{error.get('message', 'unknown error')}"
                )

            return payload["result"]

        raise RuntimeError(f"Failed Alchemy request: {method}")

    async def _get_session(self) -> ClientSession:
        if self.session is None or self.session.closed:
            self.session = ClientSession(
                timeout=ClientTimeout(total=60),
            )

        return self.session

    def _parse_transfer(
        self,
        transfer: dict[str, Any],
    ) -> IndexedTransfer:
        raw_contract = transfer.get("rawContract", {})
        raw_amount = raw_contract.get("value")
        log_index = self._parse_log_index(transfer["uniqueId"])

        if raw_amount is None:
            raise AlchemyImportError(
                "Alchemy returned an ERC-20 transfer without raw value"
            )

        amount_raw = Decimal(int(raw_amount, 16))
        timestamp = self._parse_timestamp(
            transfer.get("metadata", {}).get("blockTimestamp")
        )
        from_address = transfer["from"].lower()
        to_address = transfer["to"].lower()

        return IndexedTransfer(
            chain=self.chain,
            token_symbol=self.token.symbol,
            token_address=self.token.address,
            transaction_hash=transfer["hash"].lower(),
            log_index=log_index,
            block_number=int(transfer["blockNum"], 16),
            # The Transfers API omits block hashes. Imported ranges are
            # finalized; the checkpoint retains a canonical tip hash.
            block_hash="provider:alchemy",
            timestamp=timestamp,
            from_address=from_address,
            to_address=to_address,
            amount_raw=amount_raw,
            amount=(
                amount_raw / (Decimal(10) ** self.token.decimals)
            ),
            event_type=get_event_type(from_address, to_address),
        )

    @staticmethod
    def _parse_log_index(unique_id: str) -> int:
        _, separator, value = unique_id.rpartition(":")

        if not separator:
            raise AlchemyImportError(
                f"Alchemy returned an invalid unique ID: {unique_id}"
            )

        try:
            base = 16 if value.startswith("0x") else 10
            return int(value, base)
        except ValueError as exc:
            raise AlchemyImportError(
                f"Alchemy returned a non-log unique ID: {unique_id}"
            ) from exc

    @staticmethod
    def _parse_timestamp(value: str | None) -> datetime:
        if value is None:
            raise AlchemyImportError(
                "Alchemy returned a transfer without a block timestamp"
            )

        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).astimezone(timezone.utc)
