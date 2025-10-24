"""
Unit tests for Transaction.freeze() and Transaction.to_bytes() methods.

These tests verify the new functionality for freezing transactions and
converting them to bytes without executing them.
"""

import pytest
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId

pytestmark = pytest.mark.unit


def test_freeze_without_transaction_id_raises_error():
    """Test that freeze() raises ValueError when transaction_id is not set."""
    transaction = TransferTransaction()
    transaction.node_account_id = AccountId.from_string("0.0.3")
    
    with pytest.raises(ValueError, match="Transaction ID must be set before freezing"):
        transaction.freeze()


def test_freeze_without_node_account_id_raises_error():
    """Test that freeze() raises ValueError when node_account_id is not set."""
    transaction = TransferTransaction()
    transaction.transaction_id = TransactionId.generate(AccountId.from_string("0.0.1234"))
    
    with pytest.raises(ValueError, match="Node account ID must be set before freezing"):
        transaction.freeze()


def test_freeze_with_valid_parameters():
    """Test that freeze() works correctly when all required parameters are set."""
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
    
    # Should not raise any errors
    result = transaction.freeze()
    
    # Should return self for method chaining
    assert result is transaction
    
    # Should have transaction body bytes set
    assert len(transaction._transaction_body_bytes) > 0
    assert node_id in transaction._transaction_body_bytes


def test_freeze_is_idempotent():
    """Test that calling freeze() multiple times doesn't cause issues."""
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
    
    # Freeze multiple times
    transaction.freeze()
    transaction.freeze()
    transaction.freeze()
    
    # Should still work fine
    assert len(transaction._transaction_body_bytes) > 0


def test_to_bytes_requires_frozen_transaction():
    """Test that to_bytes() raises error if transaction is not frozen."""
    transaction = TransferTransaction()
    
    with pytest.raises(Exception, match="Transaction is not frozen"):
        transaction.to_bytes()


def test_to_bytes_returns_bytes():
    """Test that to_bytes() returns bytes after freezing and signing."""
    operator_id = AccountId.from_string("0.0.1234")
    node_id = AccountId.from_string("0.0.3")
    receiver_id = AccountId.from_string("0.0.5678")
    
    # Generate a private key for signing
    private_key = PrivateKey.generate()
    
    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100_000_000)
        .add_hbar_transfer(receiver_id, 100_000_000)
    )
    
    transaction.transaction_id = TransactionId.generate(operator_id)
    transaction.node_account_id = node_id
    
    # Freeze and sign the transaction
    transaction.freeze()
    transaction.sign(private_key)
    
    # Get bytes
    transaction_bytes = transaction.to_bytes()
    
    # Verify it's bytes
    assert isinstance(transaction_bytes, bytes)
    assert len(transaction_bytes) > 0


def test_to_bytes_produces_consistent_output():
    """Test that calling to_bytes() multiple times produces the same output."""
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
    transaction.sign(private_key)
    
    # Get bytes multiple times
    bytes1 = transaction.to_bytes()
    bytes2 = transaction.to_bytes()
    bytes3 = transaction.to_bytes()
    
    # All should be identical
    assert bytes1 == bytes2
    assert bytes2 == bytes3


def test_cannot_modify_transaction_after_freeze():
    """Test that transaction cannot be modified after freezing."""
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
    
    # Attempting to add more transfers should raise an error
    with pytest.raises(Exception, match="Transaction is immutable"):
        transaction.add_hbar_transfer(AccountId.from_string("0.0.9999"), 50_000_000)


def test_from_bytes_not_implemented():
    """Test that from_bytes() raises ValueError for invalid bytes."""
    # Create some dummy bytes
    dummy_bytes = b"dummy transaction bytes"
    
    # Should raise ValueError because the bytes are not valid protobuf
    with pytest.raises(ValueError, match="Failed to parse transaction bytes"):
        TransferTransaction.from_bytes(dummy_bytes)


def test_freeze_and_sign_workflow():
    """Test the complete workflow: create -> freeze -> sign -> to_bytes."""
    operator_id = AccountId.from_string("0.0.1234")
    node_id = AccountId.from_string("0.0.3")
    receiver_id = AccountId.from_string("0.0.5678")
    
    private_key = PrivateKey.generate()
    
    # Create transaction
    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100_000_000)
        .add_hbar_transfer(receiver_id, 100_000_000)
        .set_transaction_memo("Test transaction")
    )
    
    # Set required IDs
    transaction.transaction_id = TransactionId.generate(operator_id)
    transaction.node_account_id = node_id
    
    # Freeze
    transaction.freeze()
    
    # Sign
    transaction.sign(private_key)
    
    # Convert to bytes
    transaction_bytes = transaction.to_bytes()
    
    # Verify
    assert isinstance(transaction_bytes, bytes)
    assert len(transaction_bytes) > 0
    
    # Verify the transaction is signed
    assert transaction.is_signed_by(private_key.public_key())
