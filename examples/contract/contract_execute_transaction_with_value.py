"""
Example demonstrating contract execute with HBAR value transfer on the network.

This module shows how to execute a contract on the network by:
1. Setting up a client with operator credentials
2. Creating a file containing contract bytecode
3. Creating a contract using the file
4. Executing a contract payable function with HBAR value transfer

For a contract to receive HBAR (Hedera's native cryptocurrency), it must implement
one of the following:

1. receive() Function:
   A special function declared as `receive() external payable { }` that handles
   plain HBAR transfers when no specific function is called. This function:
   - Cannot have arguments
   - Cannot return anything
   - Must be declared as external and payable
   - Is executed when the contract receives HBAR without any function data

2. Payable Functions:
   Regular functions marked with the `payable` modifier that can accept HBAR
   as part of their execution. For example, the StatefulContract includes:
   `function setMessageAndPay(bytes32 _msg) external payable`

If a contract doesn't implement either of these, it cannot receive HBAR and
the transaction will fail.

Usage:
    # Due to the way the script is structured, it must be run as a module
    # from the project root directory

    # Run from the project root directory
    uv run -m examples.contract.contract_execute_transaction_with_value
    python -m examples.contract.contract_execute_transaction_with_value

Note:
    The example contract (StatefulContract) implements both methods:
    - A receive() function for plain HBAR transfers
    - A setMessageAndPay() function that accepts HBAR while updating a message
"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Network, PrivateKey
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_execute_transaction import (
    ContractExecuteTransaction,
)
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.contract_info_query import ContractInfoQuery
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode

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


def execute_contract_with_value():
    """
    Demonstrates executing a contract with HBAR value transfer by:
    1. Setting up client with operator account
    2. Creating a file containing stateful contract bytecode
    3. Creating a contract using the file
    4. Executing a contract with HBAR value transfer
    5. Querying the contract info to verify the balance

    The set_payable_amount() method sends HBAR from the transaction signer to the contract.
    The contract must have either a receive() function declared as `receive() external payable`
    or a specific payable function (e.g., setMessageAndPay in StatefulContract) to receive HBAR.
    Without either of these, the contract cannot receive HBAR and the transaction will fail.
    """
    client = setup_client()

    file_id = create_contract_file(client)

    contract_id = create_contract(client, file_id)

    # Execute the contract with HBAR value transfer
    # This sends 1 HBAR from the operator to the contract using method #1 (receive function)
    # described in the file documentation above.
    # The contract's receive() function will automatically handle the HBAR transfer.
    amount = Hbar(1)  # 1 HBAR sent to contract
    receipt = (
        ContractExecuteTransaction()
        .set_contract_id(contract_id)
        .set_gas(2000000)
        .set_payable_amount(amount)
        # .set_function(
        #     "setMessageAndPay", ContractFunctionParameters().add_bytes32(b"test")
        # ) # Uses method #2 (payable function)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Contract execution failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(f"Successfully executed contract {contract_id} with HBAR value transfer")
    print(f"Amount sent to contract: {amount}")

    # Verify that the contract received the HBAR by querying contract info
    info = ContractInfoQuery().set_contract_id(contract_id).execute(client)
    print(f"Contract balance: {Hbar.from_tinybars(info.balance)}")


if __name__ == "__main__":
    execute_contract_with_value()
