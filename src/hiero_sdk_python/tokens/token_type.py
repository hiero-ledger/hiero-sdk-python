"""
hiero_sdk_python.tokens.token_type.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines TokenType enum for distinguishing between fungible common tokens
and non-fungible unique tokens on the Hedera network.
"""

from enum import Enum

class TokenType(Enum):
    """Enum for Hedera token types: FUNGIBLE_COMMON or NON_FUNGIBLE_UNIQUE."""
    FUNGIBLE_COMMON = 0
    NON_FUNGIBLE_UNIQUE = 1
