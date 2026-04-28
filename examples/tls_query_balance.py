r"""

TLS Query Balance Example.

Demonstrates how to connect to the Hedera network with TLS enabled.

Required environment variables:
  - OPERATOR_ID
  - OPERATOR_KEY
Optional:
  - NETWORK (defaults to testnet)
  - VERIFY_CERTS (set to \"true\" to enforce certificate hash checks)

Run with:
  uv run examples/tls_query_balance.py
"""

import os

from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountId,
    Client,
    CryptoGetAccountBalanceQuery,
    PrivateKey,
)


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes"}


def _load_operator_credentials() -> tuple[AccountId, PrivateKey]:
    """Load operator credentials from the environment."""
    operator_id_str = os.getenv("OPERATOR_ID")
    operator_key_str = os.getenv("OPERATOR_KEY")

    if not operator_id_str or not operator_key_str:
        raise ValueError("OPERATOR_ID and OPERATOR_KEY must be set in the environment")

    operator_id = AccountId.from_string(operator_id_str)
    operator_key = PrivateKey.from_string(operator_key_str)
    return operator_id, operator_key


def setup_client() -> Client:
    """Setup Client."""
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client


def query_account_balance(client: Client, account_id: AccountId):
    """Execute a CryptoGetAccountBalanceQuery for the given account."""
    query = CryptoGetAccountBalanceQuery().set_account_id(account_id)
    balance = query.execute(client)
    print(f"Operator account {account_id} balance: {balance.hbars.to_hbars()} hbars")


def main():
    load_dotenv()

    operator_id, operator_key = _load_operator_credentials()
    client = setup_client()
    client.set_operator(operator_id, operator_key)

    query_account_balance(client, operator_id)


if __name__ == "__main__":
    main()
