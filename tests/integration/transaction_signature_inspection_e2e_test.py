from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction


def signed_transfer(env) -> TransferTransaction:
    """Freeze a transfer and sign it with the operator, so execute() adds no signature."""
    return (
        TransferTransaction()
        .add_hbar_transfer(env.operator_id, -1)
        .add_hbar_transfer(AccountId(0, 0, 3), 1)
        .freeze_with(env.client)
        .sign_with_operator(env.client)
    )


@pytest.mark.integration
def test_precomputed_hash_equals_response_hash(env):
    """Test that the hash computed before execute equals the hash of the node that received the transaction."""
    tx = signed_transfer(env)
    per_node = tx.get_transaction_hash_per_node()

    response = tx.execute(env.client, wait_for_receipt=False)

    assert response.hash == per_node[response.node_id]

    receipt = response.get_receipt(env.client)
    assert receipt.status == ResponseCode.SUCCESS, f"Transfer failed: {ResponseCode(receipt.status).name}"


@pytest.mark.integration
def test_restored_transaction_hash_and_signatures(env):
    """Test that a reviewer can read the signatures and hash of a restored transaction before submitting it."""
    tx = signed_transfer(env)
    expected_signatures = tx.get_signatures()

    restored = Transaction.from_bytes(tx.to_bytes())

    assert restored.get_signatures() == expected_signatures
    operator_public_key = env.operator_key.public_key()
    for entry in restored.signable_node_body_bytes_list:
        signature = restored.get_signatures()[entry.node_account_id][operator_public_key]
        operator_public_key.verify(signature, entry.signable_transaction_body_bytes)

    per_node = restored.get_transaction_hash_per_node()
    response = restored.execute(env.client, wait_for_receipt=False)

    assert response.hash == per_node[response.node_id]

    receipt = response.get_receipt(env.client)
    assert receipt.status == ResponseCode.SUCCESS, f"Transfer failed: {ResponseCode(receipt.status).name}"
