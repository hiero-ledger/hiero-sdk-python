"""
Contract Balance Query Example

This script demonstrates how to:
1. Set up a client connection to the Hedera network
2. Create a file containing contract bytecode
3. Create a contract
4. Query the contract balance using CryptoGetAccountBalanceQuery.set_contract_id()

Run with:
  uv run -m examples.contract.contract_balance_query
  python -m examples.contract.contract_balance_query
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    ContractCreateTransaction,
    CryptoGetAccountBalanceQuery,
    Hbar,
)

from hiero_sdk_python.contract.contract_id import ContractId

from .contracts import SIMPLE_CONTRACT_BYTECODE
from hiero_sdk_python.response_code import ResponseCode

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client() -> Client:
    print("Initializing client from environment variables...")
    try:
        client = Client.from_env()
        print(f"✅ Success! Connected as operator: {client.operator_account_id}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)
    
    return client


def create_contract(client: Client, initial_balance_tinybars: int) -> ContractId:
    """Create a contract using the bytecode file and return its ContractId."""
    bytecode = bytes.fromhex(SIMPLE_CONTRACT_BYTECODE)

    receipt = (
        ContractCreateTransaction()
        .set_bytecode(bytecode)
        .set_gas(2_000_000)
        .set_initial_balance(initial_balance_tinybars)
        .set_contract_memo("Contract for balance query example")
        .execute(client)
    )

    status_code = ResponseCode(receipt.status)
    status_name = status_code.name

    if status_name == ResponseCode.SUCCESS.name:
        print("✅ Transaction succeeded!")
    elif status_code.is_unknown:
        print(f"❓ Unknown transaction status: {status_name}")
        sys.exit(1)
    else:
        print("❌ Transaction failed!")
        sys.exit(1)

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

        initial_balance_tinybars = Hbar(1)
        contract_id = create_contract(client, initial_balance_tinybars.to_tinybars())

        print(f"✅Contract created with ID: {contract_id}")
        get_contract_balance(client, contract_id)

    except Exception as e:
        print(f"❌Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
