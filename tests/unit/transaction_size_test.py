"""
Tests for transaction size calculation methods.
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

pytestmark = pytest.mark.unit


def test_transaction_size_basic():
    """Test size() method returns the total serialized transaction size."""
    tx = TransferTransaction()
    tx.set_transaction_id(TransactionId.generate(AccountId(0, 0, 1)))
    tx.node_account_id = AccountId(0, 0, 3)
    tx.freeze()

    # size() should return the same length as to_bytes()
    tx_bytes = tx.to_bytes()
    assert tx.size() == len(tx_bytes)
    assert tx.size() > 0


def test_transaction_body_size():
    """Test body_size property returns the transaction body size only."""
    tx = TransferTransaction()
    tx.set_transaction_id(TransactionId.generate(AccountId(0, 0, 1)))
    tx.node_account_id = AccountId(0, 0, 3)
    tx.freeze()

    # body_size should be less than or equal to total size (since it excludes signatures and protobuf overhead)
    assert tx.body_size > 0
    assert tx.body_size <= tx.size()


def test_transaction_size_with_signature():
    """Test that size() includes signatures when transaction is signed."""
    private_key = PrivateKey.generate()

    tx = TransferTransaction()
    tx.set_transaction_id(TransactionId.generate(AccountId(0, 0, 1)))
    tx.node_account_id = AccountId(0, 0, 3)
    tx.freeze()

    # Get size before signing
    size_unsigned = tx.size()

    # Sign the transaction
    tx.sign(private_key)

    # Size should increase after signing due to signature
    size_signed = tx.size()
    assert size_signed > size_unsigned


def test_file_append_body_size_all_chunks_single_chunk():
    """Test body_size_all_chunks for FileAppendTransaction with single chunk."""
    tx = FileAppendTransaction()
    tx.set_file_id(FileId(0, 0, 100))
    tx.set_contents(b"small content")
    tx.set_transaction_id(TransactionId.generate(AccountId(0, 0, 1)))
    tx.node_account_id = AccountId(0, 0, 3)
    tx.freeze()

    chunk_sizes = tx.body_size_all_chunks

    # Should have exactly 1 chunk for small content
    assert len(chunk_sizes) == 1
    assert chunk_sizes[0] > 0


def test_file_append_body_size_all_chunks_multiple_chunks():
    """Test body_size_all_chunks for FileAppendTransaction with multiple chunks."""
    # Create content that requires multiple chunks (default chunk_size is 4096)
    large_content = b"x" * 10000

    tx = FileAppendTransaction()
    tx.set_file_id(FileId(0, 0, 100))
    tx.set_contents(large_content)
    tx.set_transaction_id(TransactionId.generate(AccountId(0, 0, 1)))
    tx.node_account_id = AccountId(0, 0, 3)
    tx.freeze()

    chunk_sizes = tx.body_size_all_chunks

    # Should have 3 chunks: 4096 + 4096 + 1808 = 10000 bytes
    assert len(chunk_sizes) == 3
    assert all(size > 0 for size in chunk_sizes)


def test_topic_message_body_size_all_chunks_single_chunk():
    """Test body_size_all_chunks for TopicMessageSubmitTransaction with single chunk."""
    tx = TopicMessageSubmitTransaction()
    tx.set_topic_id(TopicId(0, 0, 100))
    tx.set_message("small message")
    tx.set_transaction_id(TransactionId.generate(AccountId(0, 0, 1)))
    tx.node_account_id = AccountId(0, 0, 3)
    tx.freeze()

    chunk_sizes = tx.body_size_all_chunks

    # Should have exactly 1 chunk for small message
    assert len(chunk_sizes) == 1
    assert chunk_sizes[0] > 0


def test_topic_message_body_size_all_chunks_multiple_chunks():
    """Test body_size_all_chunks for TopicMessageSubmitTransaction with multiple chunks."""
    # Create message that requires multiple chunks (default chunk_size is 1024)
    large_message = "x" * 3000

    tx = TopicMessageSubmitTransaction()
    tx.set_topic_id(TopicId(0, 0, 100))
    tx.set_message(large_message)
    tx.set_transaction_id(TransactionId.generate(AccountId(0, 0, 1)))
    tx.node_account_id = AccountId(0, 0, 3)
    tx.freeze()

    chunk_sizes = tx.body_size_all_chunks

    # Should have 3 chunks: 1024 + 1024 + 952 = 3000 bytes
    assert len(chunk_sizes) == 3
    assert all(size > 0 for size in chunk_sizes)


def test_transaction_size_requires_frozen():
    """Test that size() and body_size require transaction to be frozen."""
    tx = TransferTransaction()

    # Should raise exception when not frozen
    with pytest.raises(Exception, match="Transaction is not frozen"):
        tx.size()

    with pytest.raises(Exception, match="Transaction is not frozen"):
        _ = tx.body_size


def test_chunked_transaction_body_size_all_chunks_requires_frozen():
    """Test that body_size_all_chunks requires transaction to be frozen."""
    tx = FileAppendTransaction()
    tx.set_file_id(FileId(0, 0, 100))
    tx.set_contents(b"content")

    # Should raise exception when not frozen
    with pytest.raises(Exception, match="Transaction is not frozen"):
        _ = tx.body_size_all_chunks
