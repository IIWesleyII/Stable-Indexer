from dataclasses import dataclass


@dataclass(frozen=True)
class StablecoinConfig:
    symbol: str
    address: str
    decimals: int


BASE_SEPOLIA_USDC = StablecoinConfig(
    symbol="USDC",
    address="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    decimals=6,
)
