"""
This module provides utilities for loading and managing smart contract bytecode.
It contains bytecode constants for contracts and configuration constants for deployment.

File Structure:
    examples/contracts/
        ContractName/
            ContractName.sol      # Original Solidity source code
            ContractName.bin      # Compiled bytecode (hex-encoded)
            ContractName.bin-runtime # Compiled bytecode (hex-encoded)

Generating Bytecode Files:
    1. Use the Solidity compiler (solc) to generate hex-encoded bytecode:
       # Make sure you are in the examples/contracts directory when running this command:
       solc --bin ContractName/ContractName.sol -o ContractName/
       # To generate the runtime bytecode, run the following command (optional):
       solc --bin-runtime ContractName/ContractName.sol -o ContractName/

    2. This creates a .bin file containing the contract's bytecode (no 0x prefix)

    3. Place the .bin file in the same directory as its source .sol file

Notes:
    - Bytecode files must be hex-encoded strings, not raw binaries
    - Each contract's bytecode is loaded into a constant (e.g. SIMPLE_CONTRACT_BYTECODE)
    - The _load_contract_bytecode() utility handles loading and validation
"""

from pathlib import Path


def _load_contract_bytecode(contract_name: str, extension: str = "bin") -> str:
    """
    Load contract bytecode from file, with proper error handling.

    Args:
        contract_name: Name of the contract (e.g., 'SimpleContract', 'StatefulContract')
        extension: Extension of the contract bytecode file (e.g., 'bin', 'bin-runtime')

    Returns:
        Contract bytecode as a string

    Raises:
        FileNotFoundError: If the contract .{extension} file is not found
        RuntimeError: If there's an error loading the bytecode
    """
    try:
        # Look for contract in the main contracts directory (relative to project root)
        contract_path = Path(__file__).parent.joinpath(
            contract_name, f"{contract_name}.{extension}"
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


# Contract bytecode constants — loaded from hex-encoded .bin files

# SimpleContract:
# A minimal contract with a static "Hello, world!" message,
# and an owner-only function to withdraw funds.
SIMPLE_CONTRACT_BYTECODE = _load_contract_bytecode("SimpleContract")

# The deployed (runtime) bytecode for SimpleContract, loaded from its .bin-runtime file.
SIMPLE_CONTRACT_RUNTIME_BYTECODE = _load_contract_bytecode(
    "SimpleContract", "bin-runtime"
)

# StatefulContract:
# Initializes a bytes32 message via constructor, stores it on-chain,
# allows the owner to update it, and supports fund withdrawal.
STATEFUL_CONTRACT_BYTECODE = _load_contract_bytecode("StatefulContract")

# ConstructorTestContract:
# Used to test constructor parameters during deployment,
# typically for verifying ABI encoding and parameter passing logic.
CONSTRUCTOR_TEST_CONTRACT_BYTECODE = _load_contract_bytecode("ConstructorTestContract")

# Contract deployment configuration
CONTRACT_DEPLOY_GAS = 2_000_000
