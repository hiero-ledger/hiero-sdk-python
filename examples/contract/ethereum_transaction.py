"""
Example demonstrating Ethereum transaction execution on the network.

This module shows how to execute a contract using Ethereum transaction by:
1. Setting up a client with operator credentials
2. Creating an alias account for ECDSA key (creating a shallow account)
3. Creating a file containing contract bytecode
4. Creating a contract using the file
5. Executing a contract function using Ethereum transaction format
6. Verifying the contract state was changed

Usage:
    # Due to the way the script is structured, it must be run as a module
    # from the project root directory

    # Run from the project root directory
    python -m examples.contract.ethereum_transaction
"""

import os
import sys

import rlp
from dotenv import load_dotenv
from eth_keys import keys

from hiero_sdk_python import AccountId, Client, Hbar, Network, PrivateKey
from hiero_sdk_python.contract.contract_call_query import ContractCallQuery
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.ethereum_transaction import EthereumTransaction
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

# Import the bytecode for a stateful smart contract (StatefulContract.sol) that can be deployed
# The contract bytecode is pre-compiled from Solidity source code
from .contracts import STATEFUL_CONTRACT_BYTECODE

load_dotenv()

network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")

    return client


def create_alias_account(client):
    """
    Create an alias account for the ECDSA key by transferring HBAR to it.

    This creates a "hollow" account controlled by the generated ECDSA key.

    Returns:
        PrivateKey: The ECDSA private key controlling the alias account
    """
    # Generate a new ECDSA private key
    alias_private_key = PrivateKey.generate_ecdsa()

    # Create an alias account ID for this key
    alias_account_id = AccountId(
        shard=0, realm=0, num=0, alias_key=alias_private_key.public_key()
    )

    print(
        f"\nCreating alias account with public key: {alias_private_key.public_key().to_string()}"
    )

    # Transfer HBAR to create a shallow account for the ECDSA key
    receipt = (
        TransferTransaction()
        .add_hbar_transfer(client.operator_account_id, -Hbar(5).to_tinybars())
        .add_hbar_transfer(alias_account_id, Hbar(5).to_tinybars())
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Failed to create alias account: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print("Successfully created alias account with 5 HBAR")
    return alias_private_key


def create_contract_file(client):
    """Create a file containing the stateful contract bytecode"""
    file_receipt = (
        FileCreateTransaction()
        .set_keys(client.operator_private_key.public_key())
        .set_contents(STATEFUL_CONTRACT_BYTECODE)
        .set_file_memo("Stateful contract bytecode file")
        .execute(client)
    )

    # Check if file creation was successful
    if file_receipt.status != ResponseCode.SUCCESS:
        print(
            f"File creation failed with status: {ResponseCode(file_receipt.status).name}"
        )
        sys.exit(1)

    return file_receipt.file_id


def create_contract(client, file_id):
    """Create a contract using the file with constructor parameters"""
    initial_message = "Initial message from constructor".encode("utf-8")
    constructor_params = ContractFunctionParameters().add_bytes32(initial_message)
    receipt = (
        ContractCreateTransaction()
        .set_admin_key(client.operator_private_key.public_key())
        .set_gas(2000000)  # 2M gas
        .set_bytecode_file_id(file_id)
        .set_constructor_parameters(constructor_params)
        .set_contract_memo("Stateful smart contract with constructor")
        .execute(client)
    )

    # Check if contract creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Contract creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(f"Contract created with ID: {receipt.contract_id}")

    return receipt.contract_id


def get_contract_message(client, contract_id):
    """Get the message from the contract"""
    # Query the contract function to verify that the message was set
    query = (
        ContractCallQuery()
        .set_contract_id(contract_id)
        .set_gas(2000000)
        .set_function("getMessage")
    )

    cost = query.get_cost(client)
    query.set_max_query_payment(cost)

    result = query.execute(client)

    # The contract returns bytes32, which we decode
    # Remove null bytes padding and decode as UTF-8 text
    message_bytes = result.get_bytes32(0).rstrip(b"\x00")
    return message_bytes.decode("utf-8")


def create_ethereum_transaction_data(contract_id, new_message, alias_private_key):
    """
    Create Ethereum transaction data for calling the contract's setMessage function.

    Args:
        contract_id: The contract ID to interact with
        new_message: The new message to set (bytes)
        alias_private_key: The ECDSA private key to sign the transaction

    Returns:
        bytes: The signed Ethereum transaction data
    """
    # Prepare function call data using ContractFunctionParameters
    call_data_bytes = (
        ContractFunctionParameters("setMessage").add_bytes32(new_message).to_bytes()
    )

    # Ethereum transaction fields - hardcoded for example simplicity
    chain_id_bytes = bytes.fromhex(
        os.getenv("CHAIN_ID", "0128")
    )  # Chain ID 296 (Testnet)
    max_priority_gas_bytes = bytes.fromhex("00")  # Zero for simplicity
    nonce_bytes = bytes.fromhex("00")  # Zero nonce
    max_gas_bytes = bytes.fromhex("d1385c7bf0")  # Max fee per gas
    gas_limit_bytes = bytes.fromhex("0249f0")  # 150k gas limit
    value_bytes = bytes.fromhex("00")  # Zero value

    # Convert ContractId to 20-byte EVM address for the Ethereum transaction 'to' field
    contract_bytes = bytes.fromhex(contract_id.to_evm_address())

    # Create the transaction list without signature components
    # EIP-1559 transaction format:
    # [chainId, nonce, maxPriorityFeePerGas, maxFeePerGas, gasLimit, to, value, data, accessList]
    transaction_list = [
        chain_id_bytes,
        nonce_bytes if nonce_bytes != b"\x00" else b"",
        max_priority_gas_bytes if max_priority_gas_bytes != b"\x00" else b"",
        max_gas_bytes if max_gas_bytes != b"\x00" else b"",
        gas_limit_bytes if gas_limit_bytes != b"\x00" else b"",
        contract_bytes if contract_bytes != b"\x00" else b"",
        value_bytes if value_bytes != b"\x00" else b"",
        call_data_bytes if call_data_bytes != b"\x00" else b"",
        [],  # empty access list
    ]

    # Encode the transaction (type 2 EIP-1559 transaction)
    message_bytes = rlp.encode(transaction_list)
    message_bytes = b"\x02" + message_bytes

    # Sign the transaction using eth_keys
    private_key_obj = keys.PrivateKey(alias_private_key.to_bytes_ecdsa_raw())
    sig = private_key_obj.sign_msg(message_bytes)

    # Add the signature to the transaction
    transaction_list = transaction_list + [sig.v, sig.r, sig.s]

    # Return the complete transaction data with type 2 prefix
    return b"\x02" + rlp.encode(transaction_list)


def execute_ethereum_transaction():
    """
    Demonstrates executing a contract using Ethereum transaction by:
    1. Setting up client with operator account
    2. Creating an alias account for ECDSA key
    3. Creating a file containing contract bytecode
    4. Creating a contract using the file
    5. Getting the current message from the contract
    6. Executing the contract via Ethereum transaction to update the message
    7. Verifying the contract state was updated
    """
    client = setup_client()

    # Create an alias account (shallow account) with ECDSA key
    alias_private_key = create_alias_account(client)

    # Create the contract file and contract
    file_id = create_contract_file(client)
    contract_id = create_contract(client, file_id)

    # Check the initial contract message
    initial_message = get_contract_message(client, contract_id)
    print(f"\nInitial contract message: '{initial_message}'")

    # Prepare a new message to set in the contract (le than 32 bytes)
    new_message = "Updated message via Eth tx!".encode("utf-8")[:32]
    new_message_string = new_message.decode("utf-8")  # For display

    print(f"\nPreparing Ethereum transaction to set message: '{new_message_string}'")

    # Create Ethereum transaction data
    transaction_data = create_ethereum_transaction_data(
        contract_id, new_message, alias_private_key
    )

    # Execute the Ethereum transaction
    receipt = EthereumTransaction().set_ethereum_data(transaction_data).execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Ethereum transaction failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print("Successfully executed Ethereum transaction")

    # Verify the message was updated
    updated_message = get_contract_message(client, contract_id)
    print(f"\nRetrieved updated message from contract: '{updated_message}'")

    # Confirm the update was successful
    if updated_message == new_message_string:
        print("\nSuccess! Message was updated via Ethereum transaction.")
    else:
        print(
            f"\nMessage update failed. Expected: '{new_message_string}', got: '{updated_message}'"
        )


if __name__ == "__main__":
    execute_ethereum_transaction()
