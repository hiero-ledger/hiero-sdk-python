"""
Unit tests for the CustomFixedFee class.
"""

import pytest
from unittest.mock import MagicMock, patch  # <-- IMPORT PATCH HERE
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.hapi.services import custom_fees_pb2
from hiero_sdk_python.tokens.custom_fee import CustomFee # Added for patch object

pytestmark = pytest.mark.unit

@pytest.fixture
def test_account_id():
    """Fixture for a sample AccountId."""
    return AccountId(4, 5, 6)

@pytest.fixture
def test_token_id():
    """Fixture for a sample TokenId."""
    return TokenId(1, 2, 3)

@pytest.fixture
def mock_client():
    """Fixture for a mock Client."""
    client = MagicMock()
    client.network.ledger_id = b"test-ledger"
    return client

def test_init_default():
    """Test the default constructor."""
    fee = CustomFixedFee()
    assert fee.amount == 0
    assert fee.denominating_token_id is None
    assert fee.fee_collector_account_id is None
    assert fee.all_collectors_are_exempt is False

def test_init_with_params(test_account_id, test_token_id):
    """Test the constructor with all parameters set."""
    fee = CustomFixedFee(
        amount=100,
        denominating_token_id=test_token_id,
        fee_collector_account_id=test_account_id,
        all_collectors_are_exempt=True
    )
    assert fee.amount == 100
    assert fee.denominating_token_id == test_token_id
    assert fee.fee_collector_account_id == test_account_id
    assert fee.all_collectors_are_exempt is True

def test_set_hbar_amount():
    """Test the set_hbar_amount method."""
    fee = CustomFixedFee(denominating_token_id=TokenId(1,1,1))
    fee.set_hbar_amount(Hbar(2))
    assert fee.amount == 200_000_000
    assert fee.denominating_token_id is None # Should be cleared

def test_set_denominating_token_id(test_token_id):
    """Test the set_denominating_token_id method."""
    fee = CustomFixedFee()
    fee.set_denominating_token_id(test_token_id)
    assert fee.denominating_token_id == test_token_id
    fee.set_denominating_token_id(None)
    assert fee.denominating_token_id is None

def test_set_denominating_token_to_same_token():
    """Test setting the denominating token to the 0.0.0 sentinel."""
    fee = CustomFixedFee()
    fee.set_denominating_token_to_same_token()
    assert fee.denominating_token_id == TokenId(0, 0, 0)

def test_proto_roundtrip_all_fields(test_account_id, test_token_id):
    """Test converting to and from protobuf with all fields."""
    original_fee = CustomFixedFee(
        amount=100,
        denominating_token_id=test_token_id,
        fee_collector_account_id=test_account_id,
        all_collectors_are_exempt=True
    )
    
    proto_fee = original_fee._to_proto()
    assert proto_fee.HasField("fixed_fee")
    assert proto_fee.fixed_fee.amount == 100
    assert proto_fee.fixed_fee.denominating_token_id == test_token_id._to_proto()
    assert proto_fee.fee_collector_account_id == test_account_id._to_proto()
    assert proto_fee.all_collectors_are_exempt is True

    new_fee = CustomFixedFee._from_proto(proto_fee)
    assert isinstance(new_fee, CustomFixedFee)
    assert new_fee == original_fee

def test_proto_roundtrip_hbar_fee(test_account_id):
    """Test converting to and from protobuf for an HBAR-denominated fee."""
    original_fee = CustomFixedFee(
        amount=500,
        denominating_token_id=None, # HBAR fee
        fee_collector_account_id=test_account_id
    )
    
    proto_fee = original_fee._to_proto()
    assert proto_fee.fixed_fee.amount == 500
    assert not proto_fee.fixed_fee.HasField("denominating_token_id")
    
    new_fee = CustomFixedFee._from_proto(proto_fee)
    assert isinstance(new_fee, CustomFixedFee)
    assert new_fee.denominating_token_id is None
    assert new_fee == original_fee

def test_to_topic_fee_proto(test_account_id, test_token_id):
    """Test the _to_topic_fee_proto method."""
    fee = CustomFixedFee(
        amount=100,
        denominating_token_id=test_token_id,
        fee_collector_account_id=test_account_id
    )
    topic_proto = fee._to_topic_fee_proto()
    
    assert isinstance(topic_proto, custom_fees_pb2.FixedCustomFee)
    assert topic_proto.fixed_fee.amount == 100
    assert topic_proto.fixed_fee.denominating_token_id == test_token_id._to_proto()
    assert topic_proto.fee_collector_account_id == test_account_id._to_proto()

def test_eq(test_account_id, test_token_id):
    """Test the __eq__ method."""
    fee1 = CustomFixedFee(
        amount=100,
        denominating_token_id=test_token_id,
        fee_collector_account_id=test_account_id
    )
    fee2 = CustomFixedFee(
        amount=100,
        denominating_token_id=test_token_id,
        fee_collector_account_id=test_account_id
    )
    fee3 = CustomFixedFee(
        amount=999, # Different amount
        denominating_token_id=test_token_id,
        fee_collector_account_id=test_account_id
    )
    fee4 = CustomFixedFee(
        amount=100,
        denominating_token_id=TokenId(0, 0, 0), # Different token
        fee_collector_account_id=test_account_id
    )
    fee5 = CustomFixedFee(
        amount=100,
        denominating_token_id=test_token_id,
        fee_collector_account_id=AccountId(9, 9, 9) # Different collector
    )

    assert fee1 == fee2
    assert fee1 != fee3
    assert fee1 != fee4
    assert fee1 != fee5
    assert fee1 != "not-a-fee"

def test_repr_all_fields(test_account_id, test_token_id):
    """Test the __repr__ method with all fields populated."""
    fee = CustomFixedFee(
        amount=100,
        denominating_token_id=test_token_id,
        fee_collector_account_id=test_account_id,
        all_collectors_are_exempt=True
    )

    # Get the repr() of the inner objects
    token_repr = repr(test_token_id)
    account_repr = repr(test_account_id)

    expected_repr = (
        f"CustomFixedFee("
        f"amount=100, "
        f"denominating_token_id={token_repr}, "
        f"fee_collector_account_id={account_repr}, "
        f"all_collectors_are_exempt=True)"
    )

    assert repr(fee) == expected_repr

def test_repr_minimal_hbar():
    """Test the __repr__ method for an HBAR fee with default exemption."""
    fee = CustomFixedFee(
        amount=5000,
        denominating_token_id=None,
        fee_collector_account_id=None
    )
    
    # all_collectors_are_exempt defaults to False
    expected_repr = (
        f"CustomFixedFee("
        f"amount=5000, "
        f"denominating_token_id=None, "
        f"fee_collector_account_id=None, "
        f"all_collectors_are_exempt=False)"
    )
    
    assert repr(fee) == expected_repr

def test_repr_default_object():
    """Test the __repr__ method for a default (empty) CustomFixedFee."""
    fee = CustomFixedFee()
    
    expected_repr = (
        f"CustomFixedFee("
        f"amount=0, "
        f"denominating_token_id=None, "
        f"fee_collector_account_id=None, "
        f"all_collectors_are_exempt=False)"
    )
    
    assert repr(fee) == expected_repr


def test_validate_checksums(mock_client):
    """Test that _validate_checksums calls validate on its ID properties."""
    # Mock the ID objects to track calls
    mock_token_id = MagicMock(spec=TokenId)
    mock_account_id = MagicMock(spec=AccountId)
    
    fee = CustomFixedFee(
        denominating_token_id=mock_token_id,
        fee_collector_account_id=mock_account_id
    )
    
    # Mock the parent class's validate method to avoid side effects
    with patch.object(CustomFee, '_validate_checksums') as mock_super_validate:
        fee._validate_checksums(mock_client)

        # Check that the parent method (for fee_collector_account_id) was called
        mock_super_validate.assert_called_once_with(mock_client)
        
        # Check that the specific validation for denominating_token_id was called
        mock_token_id.validate_checksum.assert_called_once_with(mock_client)

def test_validate_checksums_no_token_id(mock_client):
    """Test that _validate_checksums skips token validation if no token ID is set."""
    mock_account_id = MagicMock(spec=AccountId)
    
    fee = CustomFixedFee(
        denominating_token_id=None,
        fee_collector_account_id=mock_account_id
    )
    
    with patch.object(CustomFee, '_validate_checksums') as mock_super_validate:
        fee._validate_checksums(mock_client)
        
        # Parent method should still be called
        mock_super_validate.assert_called_once_with(mock_client)
        
        # No token ID, so no .validate_checksum method to call (this shouldn't error)

def test_from_proto_raises_error():
    """Test that _from_proto raises ValueError if fixed_fee is not set."""
    # Create an empty CustomFee proto
    proto_fee = custom_fees_pb2.CustomFee()
    
    with pytest.raises(ValueError, match="protobuf CustomFee has no fixed_fee set"):
        CustomFixedFee._from_proto(proto_fee)