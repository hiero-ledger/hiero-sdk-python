import pytest
from hiero_sdk_python import (
    TransactionId, 
    AccountId
)

def test_from_string_valid():
        """Test parsing a valid transaction ID string."""
        tx_id_str = "0.0.123@1234567890.123456789"
        tx_id = TransactionId.from_string(tx_id_str)
        
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
        with pytest.raises(ValueError) as exc_info:
            TransactionId.from_string(s)
        assert f"Invalid TransactionId string format: {s}" in str(exc_info.value)

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