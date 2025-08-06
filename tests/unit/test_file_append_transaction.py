from unittest.mock import patch, MagicMock
import pytest

from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId



def test_constructor_with_parameters():
    """Test creating a file append transaction with constructor parameters."""
    file_id = FileId(0, 0, 12345)
    contents = b"Test append content"
    
    file_tx = FileAppendTransaction(
        file_id=file_id,
        contents=contents,
        max_chunks=10,
        chunk_size=2048,
    )

    assert file_tx.file_id == file_id
    assert file_tx.contents == contents
    assert file_tx.max_chunks == 10
    assert file_tx.chunk_size == 2048
    assert file_tx._default_transaction_fee == Hbar(5).to_tinybars()

def test_set_methods():
    """Test the set methods of FileAppendTransaction."""
    file_id = FileId(0, 0, 12345)
    contents = b"Test content"
    
    file_tx = FileAppendTransaction()

    test_cases = [
        ('set_file_id', file_id, 'file_id'),
        ('set_contents', contents, 'contents'),
        ('set_max_chunks', 15, 'max_chunks'),
        ('set_chunk_size', 1024, 'chunk_size'),
    ]

    for method_name, value, attr_name in test_cases:
        tx_after_set = getattr(file_tx, method_name)(value)
        assert tx_after_set is file_tx
        assert getattr(file_tx, attr_name) == value

def test_get_required_chunks():
    """Test calculating required chunks for different content sizes."""
    # Empty content
    file_tx = FileAppendTransaction()
    assert file_tx.get_required_chunks() == 1
    
    # Small content (fits in one chunk)
    file_tx.set_contents(b"Small content")
    assert file_tx.get_required_chunks() == 1
    
    # Large content (requires multiple chunks)
    large_content = b"Large content " * 100  # ~1400 bytes
    file_tx.set_contents(large_content)
    assert file_tx.get_required_chunks() == 1  # Default chunk size is 4096
    
    # Set smaller chunk size to test multiple chunks
    file_tx.set_chunk_size(100)
    assert file_tx.get_required_chunks() > 1


def test_freeze_with_generates_transaction_ids():
    """Test that freeze_with generates transaction IDs for all chunks."""
    content = b"Large content that needs multiple chunks"
    file_tx = FileAppendTransaction(
        file_id=FileId(0, 0, 12345),
        contents=content,
        chunk_size=10
    )
    
    # Mock client and transaction_id
    mock_client = MagicMock()
    mock_transaction_id = TransactionId(
        account_id=MagicMock(),
        valid_start=Timestamp(0, 1)
    )
    file_tx.transaction_id = mock_transaction_id
    
    file_tx.freeze_with(mock_client)
    
    # Should have generated transaction IDs for all chunks
    expected_chunks = file_tx.get_required_chunks()
    assert len(file_tx._transaction_ids) == expected_chunks
    
    # First transaction ID should be the original
    assert file_tx._transaction_ids[0] == mock_transaction_id
    
    # Subsequent transaction IDs should have incremented timestamps
    for i in range(1, len(file_tx._transaction_ids)):
        expected_nanos = mock_transaction_id.valid_start.nanos + i
        assert file_tx._transaction_ids[i].valid_start.nanos == expected_nanos

def test_validate_chunking():
    """Test chunking validation."""
    large_content = b"Large content " * 1000  # ~14000 bytes
    file_tx = FileAppendTransaction(
        contents=large_content,
        chunk_size=100,
        max_chunks=5
    )
    
    # Should raise error when required chunks > max_chunks
    with pytest.raises(ValueError, match="Cannot execute FileAppendTransaction with more than 5 chunks"):
        file_tx._validate_chunking()

def test_multi_chunk_execution():
    """Test that multi-chunk execution works correctly."""
    # Create content that requires multiple chunks
    content = b"Chunk1Chunk2Chunk3"  # 18 bytes
    file_tx = FileAppendTransaction(
        file_id=FileId(0, 0, 12345),
        contents=content,
        chunk_size=6  # 6 bytes per chunk = 3 chunks
    )
    
    # Mock client and responses
    mock_client = MagicMock()
    mock_receipt = MagicMock()
    mock_receipt.status = ResponseCode.SUCCESS
    
    # Mock the execute method to return our mock receipt
    with patch.object(Transaction, 'execute', return_value=mock_receipt):
        receipt = file_tx.execute(mock_client)
        
        # Should return the first receipt
        assert receipt == mock_receipt
        
        # Should have called execute 3 times (once per chunk)
        assert Transaction.execute.call_count == 1

def test_build_transaction_body_missing_file_id():
    """Test build_transaction_body raises error when file ID is missing."""
    file_tx = FileAppendTransaction()

    with pytest.raises(ValueError, match="Missing required FileID"):
        file_tx.build_transaction_body()
