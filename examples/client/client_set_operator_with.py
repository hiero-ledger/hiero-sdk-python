"""
Set up a client whose operator signs through a callback instead of a private key.

`Client.set_operator_with(account_id, public_key, signer)` lets the operator key
stay in an HSM or a cloud KMS. The client then uses the signer to pay for every
transaction and query it executes.

This example simulates the HSM with a callback that wraps OPERATOR_KEY.

Usage:
    uv run examples/client/client_set_operator_with.py
    python examples/client/client_set_operator_with.py
"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountId,
    AccountInfoQuery,
    Client,
    Hbar,
    Network,
    PrivateKey,
    ResponseCode,
    Signer,
)


load_dotenv()

NETWORK_NAME = os.getenv("NETWORK", "testnet").lower()
OPERATOR_ID = os.getenv("OPERATOR_ID")
OPERATOR_KEY = os.getenv("OPERATOR_KEY")


def simulated_hsm(private_key: PrivateKey) -> Signer:
    """
    Return a signer callback standing in for an HSM or KMS.

    A real signer would send body_bytes to the HSM and return the raw signature.
    """

    def signer(body_bytes: bytes) -> bytes:
        print(f"  HSM asked to sign {len(body_bytes)} bytes")
        return private_key.sign(body_bytes)

    return signer


def setup_client() -> Client:
    """Create a client whose operator signs through the simulated HSM."""
    if not OPERATOR_ID or not OPERATOR_KEY:
        raise ValueError("OPERATOR_ID and OPERATOR_KEY environment variables are required")

    operator_id = AccountId.from_string(OPERATOR_ID)
    operator_key = PrivateKey.from_string(OPERATOR_KEY)

    # Only the public key and the callback reach the client
    client = Client(Network(NETWORK_NAME)).set_operator_with(
        operator_id, operator_key.public_key(), simulated_hsm(operator_key)
    )

    print(f"Network: {client.network.network}")
    print(f"Client initialized with signer-based operator {client.operator_account_id}")
    print(f"Operator private key held by the client: {client.operator_private_key}")
    return client


def create_account(client: Client) -> AccountId:
    """Create an account; the operator pays and signs through the HSM."""
    print("Creating an account...")
    receipt = (
        AccountCreateTransaction()
        .set_key_without_alias(PrivateKey.generate_ed25519().public_key())
        .set_initial_balance(Hbar(1))
        .execute(client)
    )
    if receipt.status != ResponseCode.SUCCESS:
        raise RuntimeError(f"Account creation failed with status: {ResponseCode(receipt.status).name}")

    print(f"Created account {receipt.account_id}")
    return receipt.account_id


def query_account_info(client: Client, account_id: AccountId) -> None:
    """Run a paid query; the query payment is signed through the HSM too."""
    print("Querying account info...")
    info = AccountInfoQuery().set_account_id(account_id).execute(client)
    print(f"Account {info.account_id} has a balance of {info.balance}")


def main():
    """
    1. Set up a client with set_operator_with() and a simulated HSM signer.

    2. Execute a transaction paid for by the signer-based operator.
    3. Execute a paid query, whose payment is signed by the same signer.
    """
    try:
        client = setup_client()

        account_id = create_account(client)
        query_account_info(client, account_id)

        client.close()

    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
