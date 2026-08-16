from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class EvmChainConfig:
    name: str
    rpc_url: str
    chain_id: int


BASE_SEPOLIA = EvmChainConfig(
    name="base-sepolia",
    rpc_url=settings.base_sepolia_rpc_url,
    chain_id=84532,
)


BASE_MAINNET = EvmChainConfig(
    name="base",
    rpc_url="https://mainnet.base.org",
    chain_id=8453,
)