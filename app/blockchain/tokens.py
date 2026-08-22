from dataclasses import dataclass


@dataclass(frozen=True)
class TokenConfig:
    symbol: str
    address: str
    decimals: int


BASE_USDC = TokenConfig(
    symbol="USDC",
    address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    decimals=6,
)


ETHEREUM_USDC = TokenConfig(
    symbol="USDC",
    address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    decimals=6,
)


ETHEREUM_USDT = TokenConfig(
    symbol="USDT",
    address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
    decimals=6,
)


SOLANA_USDC = TokenConfig(
    symbol="USDC",
    address="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    decimals=6,
)


SOLANA_USDT = TokenConfig(
    symbol="USDT",
    address="Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    decimals=6,
)


TRON_USDT = TokenConfig(
    symbol="USDT",
    address="TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    decimals=6,
)
