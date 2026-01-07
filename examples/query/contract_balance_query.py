"""
Contract Balance Query Example

This script demonstrates how to:
1. Set up a client connection to the Hedera network
2. Create a file containing contract bytecode
3. Create a contract
4. Query the contract balance using CryptoGetAccountBalanceQuery.set_contract_id()

Run with:
  uv run examples/query/contract_balance_query.py
  python examples/query/contract_balance_query.py
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Network,
    Client,
    AccountId,
    PrivateKey,
    FileCreateTransaction,
    ContractCreateTransaction,
    CryptoGetAccountBalanceQuery,
    Hbar,
)

from hiero_sdk_python.contract.contract_id import ContractId

# Use the same bytecode constants used by other contract examples
from examples.contract.contracts import SIMPLE_CONTRACT_BYTECODE  # adjust if your repo uses a different import path

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client() -> Client:
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id_str = os.getenv("OPERATOR_ID")
    operator_key_str = os.getenv("OPERATOR_KEY")
    if not operator_id_str or not operator_key_str:
        raise ValueError("❌OPERATOR_ID and OPERATOR_KEY environment variables must be set")

    operator_id = AccountId.from_string(operator_id_str)
    operator_key = PrivateKey.from_string(operator_key_str)
    client.set_operator(operator_id, operator_key)

    print(f"✅Client set up with operator id {client.operator_account_id}")
    return client


def create_contract_file(client: Client):
    """Create a file containing the contract bytecode and return its FileId (receipt.file_id)."""
    bytecode_bytes = bytes.fromhex(SIMPLE_CONTRACT_BYTECODE)

    receipt = (
        FileCreateTransaction()
        .set_contents(bytecode_bytes)
        .set_file_memo("Simple contract bytecode file")
        .execute(client)
    )
    return receipt.file_id


def create_contract(client: Client, file_id, initial_balance_tinybars: int) -> ContractId:
    """Create a contract using the bytecode file and return its ContractId."""
    receipt = (
        ContractCreateTransaction()
        .set_bytecode_file_id(file_id)
        .set_gas(100_000)
        .set_initial_balance(initial_balance_tinybars)
        .set_contract_memo("Simple smart contract")
        .execute(client)
    )
    return receipt.contract_id


def get_contract_balance(client: Client, contract_id: ContractId):
    """Query contract balance using CryptoGetAccountBalanceQuery.set_contract_id()."""
    print(f"Querying balance for contract {contract_id} ...")
    balance = CryptoGetAccountBalanceQuery().set_contract_id(contract_id).execute(client)

    print("✅Balance retrieved successfully!")
    print(f"  Contract: {contract_id}")
    print(f"  Hbars: {balance.hbars}")
    return balance


def main():
    try:
        client = setup_client()

        file_id = create_contract_file(client)
        initial_balance_tinybars = Hbar(1).to_tinybars()
        contract_id = create_contract(client, file_id, initial_balance_tinybars)

        print(f"✅Contract created with ID: {contract_id}")
        get_contract_balance(client, contract_id)

    except Exception as e:
        print(f"❌Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
