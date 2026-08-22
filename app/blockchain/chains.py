from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class EvmChainConfig:
    name: str
    rpc_url: str
    chain_id: int


@dataclass(frozen=True)
class SolanaChainConfig:
    name: str
    rpc_url: str


@dataclass(frozen=True)
class TronChainConfig:
    name: str
    api_url: str
    api_key: str


BASE_MAINNET = EvmChainConfig(
    name="base",
    rpc_url=settings.base_rpc_url or "https://mainnet.base.org",
    chain_id=8453,
)


ETHEREUM_MAINNET = EvmChainConfig(
    name="ethereum",
    rpc_url=settings.ethereum_rpc_url or "",
    chain_id=1,
)


SOLANA_MAINNET = SolanaChainConfig(
    name="solana",
    rpc_url=settings.solana_rpc_url or "",
)


TRON_MAINNET = TronChainConfig(
    name="tron",
    api_url="https://api.trongrid.io",
    api_key=settings.trongrid_api_key or "",
)
