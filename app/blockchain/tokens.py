from dataclasses import dataclass


@dataclass(frozen=True)
class TokenConfig:
    symbol: str
    address: str
    decimals: int


BASE_SEPOLIA_USDC = TokenConfig(
    symbol="USDC",
    address="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    decimals=6,
)


BASE_USDC = TokenConfig(
    symbol="USDC",
    address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    decimals=6,
)