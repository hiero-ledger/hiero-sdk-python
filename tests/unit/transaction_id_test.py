import pytest
import re
from hiero_sdk_python import (
    TransactionId, 
    AccountId
)

def test_from_string_valid():
    """Test parsing a valid transaction ID string."""
    tx_id_str = "0.0.123@1234567890.123456789"
    tx_id = TransactionId.from_string(tx_id_str)

    # Protect against breaking changes
    assert isinstance(tx_id, TransactionId)
    assert hasattr(tx_id, 'account_id')
    assert hasattr(tx_id, 'valid_start')
    assert hasattr(tx_id, 'scheduled')

    assert tx_id.account_id == AccountId(0, 0, 123)
    assert tx_id.valid_start.seconds == 1234567890
    assert tx_id.valid_start.nanos == 123456789
    assert tx_id.scheduled is False

def test_from_string_invalid_format_raises_error():
    """Test that invalid formats raise ValueError (covers the try-except block)."""
    invalid_strings = [
        "invalid_string",
        "0.0.123.123456789",  # Missing @ separator
        "0.0.123@12345",      # Missing . in timestamp
        "0.0.123@abc.def",    # Non-numeric timestamp
    ]
    
    for s in invalid_strings:
        with pytest.raises(ValueError, match=f"Invalid TransactionId string format: {re.escape(s)}"):
            TransactionId.from_string(s)

def test_hash_implementation():
    """Test __hash__ implementation coverage."""
    tx_id1 = TransactionId.from_string("0.0.1@100.1")
    tx_id2 = TransactionId.from_string("0.0.1@100.1")
    tx_id3 = TransactionId.from_string("0.0.2@100.1")
    
    # Hashes should be equal for equal objects
    assert hash(tx_id1) == hash(tx_id2)
    # Hashes should typically differ for different objects
    assert hash(tx_id1) != hash(tx_id3)
    
    # Verify usage in sets
    unique_ids = {tx_id1, tx_id2, tx_id3}
    assert len(unique_ids) == 2

def test_equality():
    """Test __eq__ implementation."""
    tx_id1 = TransactionId.from_string("0.0.1@100.1")
    tx_id2 = TransactionId.from_string("0.0.1@100.1")
    
    assert tx_id1 == tx_id2
    assert tx_id1 != "some_string"
    assert tx_id1 != TransactionId.from_string("0.0.1@100.2")

def test_to_proto_sets_scheduled():
    """Test that _to_proto sets the scheduled flag correctly."""
    tx_id = TransactionId.from_string("0.0.123@100.1")
    
    # Default is False
    proto_default = tx_id._to_proto()
    assert proto_default.scheduled is False
    
    # Set to True
    tx_id.scheduled = True
    proto_scheduled = tx_id._to_proto()
    assert proto_scheduled.scheduled is True

def test_generate():
    """Test generating a new TransactionId."""
    account_id = AccountId(0, 0, 123)
    tx_id = TransactionId.generate(account_id)
    
    # Protect against breaking changes
    assert isinstance(tx_id, TransactionId)
    assert hasattr(tx_id, 'account_id')
    assert hasattr(tx_id, 'valid_start')
    assert hasattr(tx_id, 'scheduled')
    
    assert tx_id.account_id == account_id
    assert tx_id.valid_start is not None
    assert tx_id.valid_start.seconds > 0
    assert tx_id.valid_start.nanos >= 0
    assert tx_id.scheduled is False, "Generated TransactionId should have scheduled=False by default"
    
def test_to_string():
    """Test converting TransactionId to string."""
    tx_id = TransactionId.from_string("0.0.123@1234567890.123456789")
    result = tx_id.to_string()
    
    assert isinstance(result, str)
    assert result == "0.0.123@1234567890.123456789"
    
    # Test with scheduled flag
    tx_id.scheduled = True
    result_scheduled = tx_id.to_string()
    assert "?scheduled" in result_scheduled


def test_str_method():
    """Test __str__ returns the same as to_string()."""
    tx_id = TransactionId.from_string("0.0.123@1234567890.123456789")
    
    assert str(tx_id) == tx_id.to_string()


def test_from_proto():
    """Test creating TransactionId from protobuf."""
    # Create a TransactionId and convert to proto
    original = TransactionId.from_string("0.0.123@1234567890.123456789")
    original.scheduled = True
    proto = original._to_proto()
    
    # Create from proto and verify all fields
    from_proto = TransactionId._from_proto(proto)
    
    assert isinstance(from_proto, TransactionId)
    assert from_proto.account_id == original.account_id
    assert from_proto.valid_start.seconds == original.valid_start.seconds
    assert from_proto.valid_start.nanos == original.valid_start.nanos
    assert from_proto.scheduled == original.scheduled


def test_round_trip_conversion():
    """Test that to_proto -> from_proto preserves all data."""
    original = TransactionId.from_string("0.0.999@9876543210.987654321")
    original.scheduled = True
    
    # Round trip
    proto = original._to_proto()
    recovered = TransactionId._from_proto(proto)
    
    # Verify equality
    assert recovered == original
    assert recovered.to_string() == original.to_string()
    
def test_from_string_with_scheduled_flag():
    """Test parsing a transaction ID string with scheduled flag."""
    tx_id = TransactionId.from_string("0.0.123@1234567890.123456789?scheduled")
    
    assert isinstance(tx_id, TransactionId)
    assert tx_id.account_id == AccountId(0, 0, 123)
    assert tx_id.valid_start.seconds == 1234567890
    assert tx_id.valid_start.nanos == 123456789
    assert tx_id.scheduled is True