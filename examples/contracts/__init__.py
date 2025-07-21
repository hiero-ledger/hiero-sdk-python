"""
This module contains the bytecode constants for the contracts
and configuration constants for the contracts.
"""

from .contract_utils import (  # Bytecode constants; Configuration constants
    CONTRACT_DEPLOY_GAS,
    SIMPLE_CONTRACT_BYTECODE,
    STATEFUL_CONTRACT_BYTECODE,
)

__all__ = [
    # Bytecode constants
    "SIMPLE_CONTRACT_BYTECODE",
    "STATEFUL_CONTRACT_BYTECODE",
    # Configuration constants
    "CONTRACT_DEPLOY_GAS",
]
