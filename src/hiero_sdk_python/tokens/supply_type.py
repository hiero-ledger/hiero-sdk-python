"""
hiero_sdk_python.tokens.supply_type.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines SupplyType, an enumeration of possible token supply behaviors
for Non-Fungible Tokens (NFTs).
"""

from enum import Enum

class SupplyType(Enum):
    """
    Enumeration of NFT supply models:

      - INFINITE: Tokens can be minted without limit.
      - FINITE:  Tokens have a fixed maximum supply.
    """
    INFINITE = 0
    FINITE   = 1
