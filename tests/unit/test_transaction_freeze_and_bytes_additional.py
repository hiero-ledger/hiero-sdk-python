"""
Additional unit tests for Transaction.freeze() and Transaction.to_bytes() methods.

These tests cover edge cases and clarify expected behavior.
"""

import pytest
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId

pytestmark = pytest.mark.unit


def test_to_bytes_works_without_signatures():
    """Test that to_bytes() works on a frozen but unsigned transaction."""
    operator_id = AccountId.from_string("0.0.1234")
    node_id = AccountId.from_string("0.0.3")
    receiver_id = AccountId.from_string("0.0.5678")

    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100_000_000)
        .add_hbar_transfer(receiver_id, 100_000_000)
    )

    transaction.transaction_id = TransactionId.generate(operator_id)
    transaction.node_account_id = node_id

    # Freeze but DON'T sign
    transaction.freeze()

    # Should still work - returns unsigned transaction bytes
    unsigned_bytes = transaction.to_bytes()

    assert isinstance(unsigned_bytes, bytes)
    assert len(unsigned_bytes) > 0


def test_freeze_only_builds_for_single_node():
    """Test that freeze() only builds transaction body for one node."""
    operator_id = AccountId.from_string("0.0.1234")
    node_id = AccountId.from_string("0.0.3")
    receiver_id = AccountId.from_string("0.0.5678")

    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100_000_000)
        .add_hbar_transfer(receiver_id, 100_000_000)
    )

    transaction.transaction_id = TransactionId.generate(operator_id)
    transaction.node_account_id = node_id
    transaction.freeze()

    # Should only have one node in the transaction body bytes map
    assert len(transaction._transaction_body_bytes) == 1
    assert node_id in transaction._transaction_body_bytes


def test_signed_and_unsigned_bytes_are_different():
    """Test that signed and unsigned transaction bytes differ."""
    operator_id = AccountId.from_string("0.0.1234")
    node_id = AccountId.from_string("0.0.3")
    receiver_id = AccountId.from_string("0.0.5678")

    private_key = PrivateKey.generate()

    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100_000_000)
        .add_hbar_transfer(receiver_id, 100_000_000)
    )

    transaction.transaction_id = TransactionId.generate(operator_id)
    transaction.node_account_id = node_id
    transaction.freeze()

    # Get unsigned bytes
    unsigned_bytes = transaction.to_bytes()

    # Sign the transaction
    transaction.sign(private_key)

    # Get signed bytes
    signed_bytes = transaction.to_bytes()

    # They should be different (signed has signatures)
    assert unsigned_bytes != signed_bytes
    assert len(signed_bytes) > len(unsigned_bytes)


def test_multiple_signatures_increase_size():
    """Test that adding multiple signatures increases byte size."""
    operator_id = AccountId.from_string("0.0.1234")
    node_id = AccountId.from_string("0.0.3")
    receiver_id = AccountId.from_string("0.0.5678")

    key1 = PrivateKey.generate()
    key2 = PrivateKey.generate()
    key3 = PrivateKey.generate()

    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100_000_000)
        .add_hbar_transfer(receiver_id, 100_000_000)
    )

    transaction.transaction_id = TransactionId.generate(operator_id)
    transaction.node_account_id = node_id
    transaction.freeze()

    # Get bytes with one signature
    transaction.sign(key1)
    bytes_1_sig = transaction.to_bytes()

    # Add second signature
    transaction.sign(key2)
    bytes_2_sig = transaction.to_bytes()

    # Add third signature
    transaction.sign(key3)
    bytes_3_sig = transaction.to_bytes()

    # Each should be larger than the previous
    assert len(bytes_2_sig) > len(bytes_1_sig)
    assert len(bytes_3_sig) > len(bytes_2_sig)


def test_changing_node_after_freeze_fails_for_to_bytes():
    """Test that changing node_account_id after freeze causes to_bytes() to fail."""
    operator_id = AccountId.from_string("0.0.1234")
    node_id_1 = AccountId.from_string("0.0.3")
    node_id_2 = AccountId.from_string("0.0.4")
    receiver_id = AccountId.from_string("0.0.5678")

    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100_000_000)
        .add_hbar_transfer(receiver_id, 100_000_000)
    )

    transaction.transaction_id = TransactionId.generate(operator_id)
    transaction.node_account_id = node_id_1
    transaction.freeze()

    # This should work
    bytes_node_1 = transaction.to_bytes()
    assert isinstance(bytes_node_1, bytes)

    # Change to a different node that wasn't frozen
    transaction.node_account_id = node_id_2

    # This should fail - no transaction body for node_id_2
    with pytest.raises(ValueError, match="No transaction body found for node"):
        transaction.to_bytes()


def test_from_bytes_with_invalid_protobuf():
    """Test that from_bytes() raises ValueError for invalid protobuf data."""
    dummy_bytes = b"dummy"

    # Should raise ValueError for invalid protobuf data
    with pytest.raises(ValueError, match="Failed to parse"):
        TransferTransaction.from_bytes(dummy_bytes)


def test_unsigned_transaction_can_be_signed_after_to_bytes():
    """Test that you can call to_bytes(), then sign, then to_bytes() again."""
    operator_id = AccountId.from_string("0.0.1234")
    node_id = AccountId.from_string("0.0.3")
    receiver_id = AccountId.from_string("0.0.5678")

    private_key = PrivateKey.generate()

    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100_000_000)
        .add_hbar_transfer(receiver_id, 100_000_000)
    )

    transaction.transaction_id = TransactionId.generate(operator_id)
    transaction.node_account_id = node_id
    transaction.freeze()

    # Get unsigned bytes
    unsigned_bytes = transaction.to_bytes()

    # Sign the transaction
    transaction.sign(private_key)

    # Get signed bytes - should work fine
    signed_bytes = transaction.to_bytes()

    assert unsigned_bytes != signed_bytes
    assert isinstance(signed_bytes, bytes)
