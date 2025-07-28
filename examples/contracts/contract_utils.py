"""
This module provides utilities for loading and managing smart contract bytecode.
It contains bytecode constants for contracts and configuration constants for deployment.
"""

from pathlib import Path


def _load_contract_bytecode(contract_name: str) -> str:
    """
    Load contract bytecode from file, with proper error handling.

    Args:
        contract_name: Name of the contract (e.g., 'SimpleContract', 'StatefulContract')

    Returns:
        Contract bytecode as a string

    Raises:
        FileNotFoundError: If the contract .bin file is not found
        RuntimeError: If there's an error loading the bytecode
    """
    try:
        # Look for contract in the main contracts directory (relative to project root)
        contract_path = Path(__file__).parent.joinpath(
            contract_name, f"{contract_name}.bin"
        )

        if not contract_path.exists():
            raise FileNotFoundError(
                f"Contract bytecode file not found: {contract_path}"
            )

        bytecode = contract_path.read_bytes().decode("utf-8").strip()

        if not bytecode:
            raise ValueError(f"Contract bytecode is empty for {contract_name}")

        return bytecode

    except Exception as e:
        raise RuntimeError(
            f"Failed to load contract bytecode for {contract_name}: {e}"
        ) from e


# Contract bytecode constants
SIMPLE_CONTRACT_BYTECODE = _load_contract_bytecode("SimpleContract")
STATEFUL_CONTRACT_BYTECODE = _load_contract_bytecode("StatefulContract")
CONSTRUCTOR_TEST_CONTRACT_BYTECODE = _load_contract_bytecode("ConstructorTestContract")

# Contract deployment configuration
CONTRACT_DEPLOY_GAS = 2_000_000
