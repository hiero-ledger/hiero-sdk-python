# src/hiero_sdk_python/tokens/token_cancel_airdrop_transaction.py

import warnings
# NOTE: Assuming the class name itself is TokenCancelAirdropTransaction inside the NEW file
from .token_airdrop_cancel_transaction import TokenCancelAirdropTransaction as NewTokenCancelAirdropTransaction

warnings.warn(
    "TokenCancelAirdropTransaction has been moved to token_airdrop_cancel_transaction. "
    "The old import path will be removed in a future release. Please update your imports.",
    DeprecationWarning,
    stacklevel=2
)

# Export the class under the old name for immediate compatibility
class TokenCancelAirdropTransaction(NewTokenCancelAirdropTransaction):
    pass

__all__ = ['TokenCancelAirdropTransaction']