"""
Sign a transaction with an external signer instead of a private key.

`sign_with(public_key, signer)` hands each transaction body to a callback and
attaches the signature it returns. This is how keys held in an HSM or a cloud KMS
sign transactions: the private key never enters the SDK.

This example simulates the HSM with a callback that wraps a locally generated key.

Usage:
    uv run examples/transaction/transaction_sign_with_external_signer.py
    python examples/transaction/transaction_sign_with_external_signer.py
"""

import sys

from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountId,
    Client,
    Hbar,
    PrivateKey,
    ResponseCode,
    Signer,
    TransferTransaction,
)


def setup_client() -> Client:
    """Initialize the client from the OPERATOR_ID and OPERATOR_KEY environment variables."""
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client initialized with operator {client.operator_account_id}")
    return client


def simulated_hsm(private_key: PrivateKey) -> Signer:
    """
    Return a signer callback standing in for an HSM or KMS.

    A real signer would send body_bytes to the HSM and return the raw signature:
    64 bytes for Ed25519, or the 64-byte r || s over keccak256(body_bytes) for ECDSA.
    """

    def signer(body_bytes: bytes) -> bytes:
        print(f"  HSM asked to sign {len(body_bytes)} bytes")
        return private_key.sign(body_bytes)

    return signer


def create_account(client: Client, key: PrivateKey) -> AccountId:
    """Create an account controlled by the HSM key."""
    receipt = (
        AccountCreateTransaction().set_key_without_alias(key.public_key()).set_initial_balance(Hbar(2)).execute(client)
    )
    if receipt.status != ResponseCode.SUCCESS:
        raise RuntimeError(f"Account creation failed with status: {ResponseCode(receipt.status).name}")

    print(f"Created account {receipt.account_id} with an ECDSA key held by the simulated HSM")
    return receipt.account_id


def transfer_with_external_signer(client: Client, account_id: AccountId, key: PrivateKey) -> None:
    """Transfer HBAR out of the HSM account, signing through the callback."""
    tx = (
        TransferTransaction()
        .add_hbar_transfer(account_id, -Hbar(1).to_tinybars())
        .add_hbar_transfer(client.operator_account_id, Hbar(1).to_tinybars())
        .freeze_with(client)
    )

    # The signer is called once per transaction body, i.e. once per node
    tx.sign_with(key.public_key(), simulated_hsm(key))
    print(f"Transaction signed by the HSM key: {tx.is_signed_by(key.public_key())}")

    # The operator pays the fee, so execute() adds the operator signature
    receipt = tx.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        raise RuntimeError(f"Transfer failed with status: {ResponseCode(receipt.status).name}")

    print(f"Transfer succeeded: {receipt.status == ResponseCode.SUCCESS}")


def main():
    """
    1. Set up a client with an operator.

    2. Create an account whose key lives in a (simulated) HSM.
    3. Transfer HBAR from that account, signing with sign_with() instead of sign().
    """
    try:
        client = setup_client()
        hsm_key = PrivateKey.generate_ecdsa()

        account_id = create_account(client, hsm_key)
        transfer_with_external_signer(client, account_id, hsm_key)

    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
