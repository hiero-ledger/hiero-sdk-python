"""
Inspect a signed transaction before submitting it.

Once a transaction is frozen you can read:
- `signable_node_body_bytes_list`: the exact bytes each node expects to be signed,
  e.g. to send to an HSM or to a co-signer for review.
- `get_signatures()`: who has signed, per node.
- `get_transaction_hash()` / `get_transaction_hash_per_node()`: the transaction hash,
  known before submission. It covers the signatures, so compute it after the last one.

Usage:
    uv run examples/transaction/transaction_get_signatures_and_hash.py
    python examples/transaction/transaction_get_signatures_and_hash.py
"""

import sys

from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountId,
    Client,
    Hbar,
    PrivateKey,
    ResponseCode,
    TransferTransaction,
)


def setup_client() -> Client:
    """Initialize the client from the OPERATOR_ID and OPERATOR_KEY environment variables."""
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client initialized with operator {client.operator_account_id}")
    return client


def create_account(client: Client, key: PrivateKey) -> AccountId:
    """Create an account controlled by key, funded with 2 HBAR."""
    receipt = (
        AccountCreateTransaction().set_key_without_alias(key.public_key()).set_initial_balance(Hbar(2)).execute(client)
    )
    if receipt.status != ResponseCode.SUCCESS:
        raise RuntimeError(f"Account creation failed with status: {ResponseCode(receipt.status).name}")

    print(f"Created account {receipt.account_id}")
    return receipt.account_id


def build_transfer(client: Client, account_id: AccountId) -> TransferTransaction:
    """Build a transfer that both the account and the operator (the fee payer) must sign."""
    return (
        TransferTransaction()
        .add_hbar_transfer(account_id, -Hbar(1).to_tinybars())
        .add_hbar_transfer(client.operator_account_id, Hbar(1).to_tinybars())
        .freeze_with(client)
    )


def print_signable_bodies(tx: TransferTransaction) -> None:
    """Print the bodies a signer would be asked to sign: one per node."""
    entries = tx.signable_node_body_bytes_list
    print(f"\nThe transaction has {len(entries)} signable bodies, one per node:")
    for entry in entries:
        print(
            f"  node {entry.node_account_id}, transaction {entry.transaction_id}: "
            f"{len(entry.signable_transaction_body_bytes)} bytes"
        )


def print_signatures(tx: TransferTransaction) -> None:
    """Print who has signed the body for each node."""
    print("\nSignatures per node:")
    for node_account_id, signatures in tx.get_signatures().items():
        signers = ", ".join(f"{public_key.to_string_raw()[:12]}..." for public_key in signatures) or "none"
        print(f"  node {node_account_id}: {len(signatures)} signature(s) from {signers}")


def main() -> None:
    """
    1. Create an account whose key co-signs a transfer.
    2. Freeze the transfer and list the bodies each node expects to be signed.
    3. Sign with the account key and the operator, then read back the signatures.
    4. Compute the transaction hash before submitting, and compare it with the response.
    """
    try:
        client = setup_client()
        account_key = PrivateKey.generate_ecdsa()
        account_id = create_account(client, account_key)

        tx = build_transfer(client, account_id)
        print_signable_bodies(tx)
        print_signatures(tx)

        # Sign with the operator now; otherwise execute() would add its signature and change the hash
        tx.sign(account_key)
        tx.sign_with_operator(client)
        print_signatures(tx)

        hash_per_node = tx.get_transaction_hash_per_node()
        print(f"\nHash for the first node, before submitting: {tx.get_transaction_hash().hex()}")

        response = tx.execute(client, wait_for_receipt=False)
        print(f"Hash returned by node {response.node_id}: {response.hash.hex()}")
        if response.hash != hash_per_node[response.node_id]:
            raise RuntimeError("The precomputed hash does not match the response hash")
        print("The precomputed hash matches the response hash")

        receipt = response.get_receipt(client)
        if receipt.status != ResponseCode.SUCCESS:
            raise RuntimeError(f"Transfer failed with status: {ResponseCode(receipt.status).name}")
        print(f"Transfer status: {ResponseCode(receipt.status).name}")

    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
