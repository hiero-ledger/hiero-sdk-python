"""
TLS Query Balance Example

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
    Network,
    Client,
    AccountId,
    PrivateKey,
    CryptoGetAccountBalanceQuery,
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
    """Create and configure a client with TLS enabled using env settings."""
    network_name = os.getenv("NETWORK", "testnet")
    verify_certs = _bool_env("VERIFY_CERTS", True)

    network = Network(network_name)
    client = Client(network)

    # Enable TLS for hosted networks (mainnet, testnet, previewnet)
    # Disable TLS for local networks (localhost, solo, local)
    hosted_networks = ("mainnet", "testnet", "previewnet")
    local_networks = ("localhost", "solo", "local")

    if network_name.lower() in hosted_networks:
        client.set_transport_security(True)
    elif network_name.lower() in local_networks:
        client.set_transport_security(False)
    # For custom networks, use Network's default (disabled)

    client.set_verify_certificates(verify_certs)
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
