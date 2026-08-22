from app.blockchain.chains import BASE_MAINNET
from app.blockchain.evm import EvmIndexer
from app.blockchain.tokens import BASE_USDC


class BaseIndexer(EvmIndexer):
    def __init__(self) -> None:
        super().__init__(
            chain=BASE_MAINNET,
            tokens=(BASE_USDC,),
        )
