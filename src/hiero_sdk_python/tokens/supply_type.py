"""
hiero_sdk_python.tokens.supply_type.py.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines SupplyType, an enumeration of possible token supply behaviors
for Non-Fungible Tokens (NFTs).
"""

from __future__ import annotations

from enum import Enum

from hiero_sdk_python.hapi.services import basic_types_pb2


class SupplyType(Enum):
    """
    Enumeration of NFT supply models:

      - INFINITE: Tokens can be minted without limit.
      - FINITE:  Tokens have a fixed maximum supply.
    """

    INFINITE = 0
    FINITE = 1

    @staticmethod
    def _from_proto(proto: basic_types_pb2.TokenSupplyType) -> SupplyType:
        """Create token supply type from prorobuf message."""
        if proto == basic_types_pb2.TokenSupplyType.FINITE:
            return SupplyType.FINITE
        if proto == basic_types_pb2.TokenSupplyType.INFINITE:
            return SupplyType.INFINITE

        raise ValueError(f"Invalid SupplyType: {proto}")
