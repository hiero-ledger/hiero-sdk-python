"""
Unit tests for batch_key accepting both PrivateKey and PublicKey.
"""

import pytest
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction


def test_set_batch_key_with_private_key():
    """Test that batch_key can be set with PrivateKey."""
    private_key = PrivateKey.generate_ed25519()
    transaction = TransferTransaction()
    
    result = transaction.set_batch_key(private_key)
    
    assert transaction.batch_key == private_key
    assert result == transaction  # Check method chaining


def test_set_batch_key_with_public_key():
    """Test that batch_key can be set with PublicKey."""
    private_key = PrivateKey.generate_ed25519()
    public_key = private_key.public_key()
    transaction = TransferTransaction()
    
    result = transaction.set_batch_key(public_key)
    
    assert transaction.batch_key == public_key
    assert result == transaction  # Check method chaining


def test_batch_key_type_annotation():
    """Test that batch_key accepts both PrivateKey and PublicKey types."""
    transaction = TransferTransaction()
    
    # Test with PrivateKey
    private_key = PrivateKey.generate_ecdsa()
    transaction.set_batch_key(private_key)
    assert isinstance(transaction.batch_key, PrivateKey)
    
    # Test with PublicKey
    public_key = private_key.public_key()
    transaction.set_batch_key(public_key)
    assert isinstance(transaction.batch_key, PublicKey)


def test_batch_key_none_by_default():
    """Test that batch_key is None by default."""
    transaction = TransferTransaction()
    assert transaction.batch_key is None
