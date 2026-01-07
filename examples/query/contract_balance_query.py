"""
Contract Balance Query Example

This script demonstrates how to query the balance of a *contract* using:
- CryptoGetAccountBalanceQuery().set_contract_id(...)

Run with:
  uv run examples/query/contract_balance_query.py
  python examples/query/contract_balance_query.py

Environment variables required:
- OPERATOR_ID
- OPERATOR_KEY
Optional:
- NETWORK (default: testnet)
- CONTRACT_ID (e.g. "0.0.1234")
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import Network, Client, AccountId, PrivateKey
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.contract.contract_id import ContractId

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """
    Initialize and configure the Hiero SDK client with operator credentials.
    """
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id_str = os.getenv("OPERATOR_ID")
    operator_key_str = os.getenv("OPERATOR_KEY")

    if not operator_id_str or not operator_key_str:
        raise ValueError("OPERATOR_ID and OPERATOR_KEY environment variables must be set")

    operator_id = AccountId.from_string(operator_id_str)
    operator_key = PrivateKey.from_string(operator_key_str)
    client.set_operator(operator_id, operator_key)

    print(f"Client set up with operator id {client.operator_account_id}")
    return client


def get_contract_balance(client: Client, contract_id: ContractId):
    """
    Query and retrieve the HBAR balance of a contract.

    Use account_id when you want an *account* balance.
    Use contract_id when you want a *contract* balance (smart contract entity).
    """
    print(f"Querying balance for contract {contract_id} ...")

    balance = CryptoGetAccountBalanceQuery().set_contract_id(contract_id).execute(client)

    # AccountBalance object: print a friendly summary
    print("✓ Balance retrieved successfully!")
    print(f"  Contract: {contract_id}")
    print(f"  Hbars: {balance.hbars}")
    if getattr(balance, "token_balances", None):
        print(f"  Token balances entries: {len(balance.token_balances)}")
    return balance


def main():
    try:
        client = setup_client()

        contract_id_str = os.getenv("CONTRACT_ID")
        if not contract_id_str:
            raise ValueError("CONTRACT_ID environment variable must be set (e.g. '0.0.1234')")

        contract_id = ContractId.from_string(contract_id_str)

        # Uncommenting the following would raise due to oneof constraints:
        # query = CryptoGetAccountBalanceQuery(account_id=client.operator_account_id, contract_id=contract_id)
        # query.execute(client)

        get_contract_balance(client, contract_id)

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
