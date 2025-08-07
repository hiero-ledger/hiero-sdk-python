"""
This module contains the bytecode constants for the contracts
and configuration constants for the contracts.
"""

from .contract_utils import (  # Bytecode constants; Configuration constants
    CONTRACT_DEPLOY_GAS,
    SIMPLE_CONTRACT_BYTECODE,
    STATEFUL_CONTRACT_BYTECODE,
    CONSTRUCTOR_TEST_CONTRACT_BYTECODE,
    SIMPLE_CONTRACT_RUNTIME_BYTECODE,
    CONTRACT_UPDATE_BYTECODE,
)

__all__ = [
    # Bytecode constants
    "SIMPLE_CONTRACT_BYTECODE",
    "STATEFUL_CONTRACT_BYTECODE",
    "CONSTRUCTOR_TEST_CONTRACT_BYTECODE",
    "SIMPLE_CONTRACT_RUNTIME_BYTECODE",
    # Configuration constants
    "CONTRACT_DEPLOY_GAS",
    "CONTRACT_UPDATE_BYTECODE",
]
