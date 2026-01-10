"""
hiero_sdk_python.tokens.token_type.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenType enum for distinguishing between fungible common tokens
and non-fungible unique tokens on Hedera network.
"""

from enum import Enum

class TokenType(Enum):
    """
    Token type for Hedera tokens.
    
    Determines whether a token represents divisible, interchangeable units
    or unique, individually identifiable assets.
    
    Attributes:
        FUNGIBLE_COMMON: Interchangeable tokens where each unit is equal.
            All tokens are identical and can be divided into smaller units.
            Used for currencies, utility tokens, or any asset where
            individual tokens are indistinguishable from each other.
            
        NON_FUNGIBLE_UNIQUE: Unique tokens where each unit is distinct.
            Each token has its own metadata and identity.
            Used for NFTs, collectibles, or any asset where
            individual tokens have unique properties and cannot be replaced
            by other tokens of the same type.
    
    Example:
        >>> # Creating a fungible token (like a currency)
        >>> token_type = TokenType.FUNGIBLE_COMMON
        >>> print(f"Token type: {token_type}")
        Token type: TokenType.FUNGIBLE_COMMON
        
        >>> # Creating a non-fungible token (like an NFT)
        >>> token_type = TokenType.NON_FUNGIBLE_UNIQUE
        >>> print(f"Token type: {token_type}")
        Token type: TokenType.NON_FUNGIBLE_UNIQUE
    """
    
    FUNGIBLE_COMMON = 0
    NON_FUNGIBLE_UNIQUE = 1
