"""
hiero_sdk_python.tokens.token_type.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenType enum for distinguishing between fungible common tokens
and non-fungible unique tokens on the Hedera network.
"""

from enum import Enum

class TokenType(Enum):
    """
    Token type for Hedera tokens:

• FUNGIBLE_COMMON - Interchangeable tokens where each unit is equal.
                          Examples: cryptocurrencies, utility tokens, stablecoins.
                          Use for tokens where units can be divided and mixed freely.
      
      • NON_FUNGIBLE_UNIQUE - Unique tokens where each token is distinct and
                               cannot be replaced. Examples: NFTs, digital collectibles,
                               unique assets. Each token has its own metadata and
                               identity.

    This enum determines whether a token represents a divisible, interchangeable
    asset or a collection of unique, non-interchangeable assets.
    """
    FUNGIBLE_COMMON = 0
    NON_FUNGIBLE_UNIQUE = 1
