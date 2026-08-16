from app.blockchain.chains import BASE_SEPOLIA
from app.blockchain.evm import EvmIndexer
from app.blockchain.tokens import BASE_SEPOLIA_USDC


class BaseSepoliaIndexer(EvmIndexer):
    def __init__(self) -> None:
        super().__init__(
            chain=BASE_SEPOLIA,
            token=BASE_SEPOLIA_USDC,
        )