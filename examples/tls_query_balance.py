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


def main():
    load_dotenv()

    network_name = os.getenv("NETWORK", "testnet")
    operator_id_str = os.getenv("OPERATOR_ID")
    operator_key_str = os.getenv("OPERATOR_KEY")

    if not operator_id_str or not operator_key_str:
        raise ValueError("OPERATOR_ID and OPERATOR_KEY must be set in the environment")

    network = Network(network_name)
    client = Client(network)

    # Enable TLS for consensus nodes. Mirror nodes already require TLS.
    client.set_transport_security(False)

    verify_certs = _bool_env("VERIFY_CERTS", True)
    client.set_verify_certificates(verify_certs)

    operator_id = AccountId.from_string(operator_id_str)
    operator_key = PrivateKey.from_string(operator_key_str)
    client.set_operator(operator_id, operator_key)

    balance = CryptoGetAccountBalanceQuery().set_account_id(operator_id).execute(client)
    print(f"Operator account {operator_id} balance: {balance.hbars.to_hbars()} hbars")


if __name__ == "__main__":
    main()


