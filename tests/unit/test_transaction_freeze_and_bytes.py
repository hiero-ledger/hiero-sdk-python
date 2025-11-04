"""
Unit tests for Transaction.freeze() and Transaction.to_bytes() methods.

These tests verify the new functionality for freezing transactions and
converting them to bytes without executing them, including edge cases
and expected behavior.
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


def test_from_bytes_invalid_input():
    """Test that from_bytes() raises ValueError for invalid input."""
    # Test with non-bytes input
    with pytest.raises(ValueError, match="must be bytes"):
        TransferTransaction.from_bytes("not bytes")

    # Test with empty bytes
    with pytest.raises(ValueError, match="cannot be empty"):
        TransferTransaction.from_bytes(b"")

    # Test with invalid protobuf bytes
    with pytest.raises(ValueError, match="Failed to parse"):
        TransferTransaction.from_bytes(b"invalid protobuf data")


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


def test_from_bytes_round_trip_unsigned():
    """Test round-trip serialization of unsigned transaction."""
    operator_id = AccountId.from_string("0.0.1234")
    node_id = AccountId.from_string("0.0.3")
    receiver_id = AccountId.from_string("0.0.5678")

    # Create and freeze transaction
    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100_000_000)
        .add_hbar_transfer(receiver_id, 100_000_000)
        .set_transaction_memo("Test memo")
    )

    transaction.transaction_id = TransactionId.generate(operator_id)
    transaction.node_account_id = node_id
    transaction.freeze()

    # Serialize to bytes
    transaction_bytes = transaction.to_bytes()

    # Deserialize from bytes
    restored_transaction = TransferTransaction.from_bytes(transaction_bytes)

    # Verify common fields
    assert restored_transaction.transaction_id == transaction.transaction_id
    assert restored_transaction.node_account_id == transaction.node_account_id
    assert restored_transaction.memo == transaction.memo
    # When transaction_fee is None, it uses the default fee in the protobuf
    # So the restored transaction will have the default fee value
    assert restored_transaction.transaction_fee == 100_000_000  # Default fee for TransferTransaction

    # Verify transfers
    assert len(restored_transaction.hbar_transfers) == 2
    assert restored_transaction.hbar_transfers[0].account_id == operator_id
    assert restored_transaction.hbar_transfers[0].amount == -100_000_000
    assert restored_transaction.hbar_transfers[1].account_id == receiver_id
    assert restored_transaction.hbar_transfers[1].amount == 100_000_000

    # Verify transaction is frozen
    assert len(restored_transaction._transaction_body_bytes) > 0

    # Verify round-trip produces identical bytes
    restored_bytes = restored_transaction.to_bytes()
    assert transaction_bytes == restored_bytes


def test_from_bytes_round_trip_signed():
    """Test round-trip serialization of signed transaction."""
    operator_id = AccountId.from_string("0.0.1234")
    node_id = AccountId.from_string("0.0.3")
    receiver_id = AccountId.from_string("0.0.5678")

    private_key = PrivateKey.generate()

    # Create, freeze, and sign transaction
    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -200_000_000)
        .add_hbar_transfer(receiver_id, 200_000_000)
        .set_transaction_memo("Signed transaction")
    )

    transaction.transaction_id = TransactionId.generate(operator_id)
    transaction.node_account_id = node_id
    transaction.freeze()
    transaction.sign(private_key)

    # Serialize to bytes
    transaction_bytes = transaction.to_bytes()

    # Deserialize from bytes
    restored_transaction = TransferTransaction.from_bytes(transaction_bytes)

    # Verify fields
    assert restored_transaction.transaction_id == transaction.transaction_id
    assert restored_transaction.node_account_id == transaction.node_account_id
    assert restored_transaction.memo == "Signed transaction"

    # Verify transfers
    assert len(restored_transaction.hbar_transfers) == 2

    # Verify signature is preserved
    assert restored_transaction.is_signed_by(private_key.public_key())

    # Verify round-trip produces identical bytes
    restored_bytes = restored_transaction.to_bytes()
    assert transaction_bytes == restored_bytes


def test_from_bytes_round_trip_multiple_signatures():
    """Test round-trip serialization with multiple signatures."""
    operator_id = AccountId.from_string("0.0.1234")
    node_id = AccountId.from_string("0.0.3")
    receiver_id = AccountId.from_string("0.0.5678")

    key1 = PrivateKey.generate()
    key2 = PrivateKey.generate()
    key3 = PrivateKey.generate()

    # Create transaction
    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -300_000_000)
        .add_hbar_transfer(receiver_id, 300_000_000)
    )

    transaction.transaction_id = TransactionId.generate(operator_id)
    transaction.node_account_id = node_id
    transaction.freeze()

    # Sign with multiple keys
    transaction.sign(key1)
    transaction.sign(key2)
    transaction.sign(key3)

    # Serialize to bytes
    transaction_bytes = transaction.to_bytes()

    # Deserialize from bytes
    restored_transaction = TransferTransaction.from_bytes(transaction_bytes)

    # Verify all signatures are preserved
    assert restored_transaction.is_signed_by(key1.public_key())
    assert restored_transaction.is_signed_by(key2.public_key())
    assert restored_transaction.is_signed_by(key3.public_key())

    # Verify round-trip produces identical bytes
    restored_bytes = restored_transaction.to_bytes()
    assert transaction_bytes == restored_bytes


def test_from_bytes_preserves_all_common_fields():
    """Test that from_bytes preserves all common transaction fields."""
    operator_id = AccountId.from_string("0.0.1234")
    node_id = AccountId.from_string("0.0.3")
    receiver_id = AccountId.from_string("0.0.5678")

    # Create transaction with all common fields set
    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100_000_000)
        .add_hbar_transfer(receiver_id, 100_000_000)
        .set_transaction_memo("Comprehensive test")
    )

    transaction.transaction_id = TransactionId.generate(operator_id)
    transaction.node_account_id = node_id
    transaction.transaction_fee = 5_000_000  # Custom fee
    transaction.transaction_valid_duration = 180  # 3 minutes
    transaction.generate_record = True

    transaction.freeze()

    # Serialize and deserialize
    transaction_bytes = transaction.to_bytes()
    restored_transaction = TransferTransaction.from_bytes(transaction_bytes)

    # Verify all common fields
    assert restored_transaction.transaction_id == transaction.transaction_id
    assert restored_transaction.node_account_id == transaction.node_account_id
    assert restored_transaction.transaction_fee == 5_000_000
    assert restored_transaction.transaction_valid_duration == 180
    assert restored_transaction.generate_record == True
    assert restored_transaction.memo == "Comprehensive test"

    # Verify round-trip
    assert transaction.to_bytes() == restored_transaction.to_bytes()


def test_from_bytes_external_signing_workflow():
    """Test the external signing workflow: create unsigned -> restore -> sign -> restore."""
    operator_id = AccountId.from_string("0.0.1234")
    node_id = AccountId.from_string("0.0.3")
    receiver_id = AccountId.from_string("0.0.5678")

    # Step 1: Create unsigned transaction (e.g., on online system)
    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100_000_000)
        .add_hbar_transfer(receiver_id, 100_000_000)
    )

    transaction.transaction_id = TransactionId.generate(operator_id)
    transaction.node_account_id = node_id
    transaction.freeze()

    unsigned_bytes = transaction.to_bytes()

    # Step 2: Restore on signing system (e.g., HSM or hardware wallet)
    tx_for_signing = TransferTransaction.from_bytes(unsigned_bytes)

    # Verify it's not signed yet
    private_key = PrivateKey.generate()
    assert not tx_for_signing.is_signed_by(private_key.public_key())

    # Sign the transaction
    tx_for_signing.sign(private_key)
    assert tx_for_signing.is_signed_by(private_key.public_key())

    signed_bytes = tx_for_signing.to_bytes()

    # Step 3: Restore signed transaction on original system
    final_tx = TransferTransaction.from_bytes(signed_bytes)

    # Verify signature is preserved
    assert final_tx.is_signed_by(private_key.public_key())

    # Verify all fields are still correct
    assert final_tx.transaction_id == transaction.transaction_id
    assert final_tx.node_account_id == transaction.node_account_id
    assert len(final_tx.hbar_transfers) == 2


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
