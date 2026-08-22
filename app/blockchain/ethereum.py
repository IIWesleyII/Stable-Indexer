from app.blockchain.chains import ETHEREUM_MAINNET
from app.blockchain.evm import EvmIndexer
from app.blockchain.tokens import ETHEREUM_USDC
from app.blockchain.tokens import ETHEREUM_USDT


class EthereumIndexer(EvmIndexer):
    def __init__(self) -> None:
        if not ETHEREUM_MAINNET.rpc_url:
            raise RuntimeError(
                "ETHEREUM_RPC_URL is required for Ethereum indexing"
            )

        super().__init__(
            chain=ETHEREUM_MAINNET,
            tokens=(
                ETHEREUM_USDC,
                ETHEREUM_USDT,
            ),
        )
