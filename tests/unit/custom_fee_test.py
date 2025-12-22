from hiero_sdk_python.client.client import Client
import pytest
import warnings
from unittest import mock
from hiero_sdk_python.tokens.custom_fee import CustomFee
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId


pytestmark = pytest.mark.unit

def test_custom_fixed_fee_proto_round_trip():
    """Ensure CustomFixedFee protobuf serialization and deserialization behave correctly."""
    fee = CustomFixedFee(
        amount=100,
        denominating_token_id=TokenId(0, 0, 123),
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=True,
    )

    proto = fee._to_proto()
    new_fee = CustomFixedFee._from_proto(proto)

    assert isinstance(new_fee, CustomFixedFee)
    assert new_fee.amount == 100
    assert new_fee.denominating_token_id == TokenId(0, 0, 123)
    assert new_fee.fee_collector_account_id == AccountId(0, 0, 456)
    assert new_fee.all_collectors_are_exempt is True

def test_custom_fixed_fee_str():
    """Test the string representation of CustomFixedFee."""
    fee = CustomFixedFee(
        amount=100,
        denominating_token_id=TokenId(0, 0, 123),
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=False,
    )

    fee_str = fee.__str__()

    # Basic checks
    assert "CustomFixedFee" in fee_str
    assert "Amount" in fee_str
    assert "Denominating Token Id" in fee_str
    assert "Fee Collector Account Id" in fee_str
    assert "All Collectors Are Exempt" in fee_str

    # Key-value extraction
    kv = {}
    for ln in fee_str.splitlines()[1:]:
        if "=" in ln:
            key, val = ln.split("=", 1)
            kv[key.strip()] = val.strip()

    expected = {
        "Amount": "100",
        "Denominating Token Id": "0.0.123",
        "Fee Collector Account Id": "0.0.456",
        "All Collectors Are Exempt": "False",
    }

    for key, val in expected.items():
        assert kv[key] == val, f"{key} incorrect in string representation"


def test_custom_fractional_fee_str():
    """Test the string representation of CustomFractionalFee."""
    fee = CustomFractionalFee(
        numerator=1,
        denominator=5,
        min_amount=10,
        max_amount=1000,
        assessment_method=FeeAssessmentMethod.INCLUSIVE,
        fee_collector_account_id=AccountId(0, 0, 789),
        all_collectors_are_exempt=False,
    )

    fee_str = fee.__str__()

    assert "CustomFractionalFee" in fee_str
    assert "Fee Collector Account Id  = 0.0.789" in fee_str
    assert "Numerator                 = 1" in fee_str
    assert "Denominator               = 5" in fee_str
    assert "Assessment Method         = FeeAssessmentMethod.INCLUSIVE" in fee_str
    assert "Min Amount                = 10" in fee_str
    assert "Max Amount                = 1000" in fee_str

    kv = {}
    for ln in fee_str.splitlines()[1:]:
        if "=" in ln:
            key, val = ln.split("=", 1)
            kv[key.strip()] = val.strip()

    expected = {
        "Numerator": "1",
        "Denominator": "5",
        "Min Amount": "10",
        "Max Amount": "1000",
    }
    for key, val in expected.items():
        assert kv[key] == val, f"{key} incorrect in string representation"

    assert "INCLUSIVE" in kv["Assessment Method"]
    assert "0.0.789" in kv["Fee Collector Account Id"]
    assert kv["All Collectors Are Exempt"] in ("False", "false")

def test_custom_fractional_fee():
    fee = CustomFractionalFee(
        numerator=1,
        denominator=10,
        min_amount=1,
        max_amount=100,
        assessment_method=FeeAssessmentMethod.EXCLUSIVE,
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=False,
    )

    proto = fee._to_proto()  # Changed from _to_protobuf
    new_fee = CustomFractionalFee._from_proto(proto)  # Changed from CustomFee._from_protobuf

    assert isinstance(new_fee, CustomFractionalFee)
    assert new_fee.numerator == 1
    assert new_fee.denominator == 10
    assert new_fee.min_amount == 1
    assert new_fee.max_amount == 100
    assert new_fee.assessment_method == FeeAssessmentMethod.EXCLUSIVE
    assert new_fee.fee_collector_account_id == AccountId(0, 0, 456)
    assert new_fee.all_collectors_are_exempt is False

def test_custom_royalty_fee():
    fallback_fee = CustomFixedFee(
        amount=50,
        denominating_token_id=TokenId(0, 0, 789),
    )
    fee = CustomRoyaltyFee(
        numerator=5,
        denominator=100,
        fallback_fee=fallback_fee,
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=True,
    )

    proto = fee._to_proto()  # Changed from _to_protobuf
    new_fee = CustomRoyaltyFee._from_proto(proto)  # Changed from CustomFee._from_protobuf

    assert isinstance(new_fee, CustomRoyaltyFee)
    assert new_fee.numerator == 5
    assert new_fee.denominator == 100
    assert new_fee.fee_collector_account_id == AccountId(0, 0, 456)
    assert new_fee.all_collectors_are_exempt is True
    assert isinstance(new_fee.fallback_fee, CustomFixedFee)
    assert new_fee.fallback_fee.amount == 50
    assert new_fee.fallback_fee.denominating_token_id == TokenId(0, 0, 789)

@pytest.mark.parametrize(
        "custom_royalty_fee, expected_str",
        [
            (
                CustomRoyaltyFee(
                   numerator=3,
                   denominator=20,
                   fallback_fee=None,
                   fee_collector_account_id=None,
                   all_collectors_are_exempt=True,
                ),
                "\n".join([
                    "CustomRoyaltyFee:",
                    "   Numerator = 3",
                    "   Denominator = 20",
                    "   Fallback Fee Amount = None",
                    "   Fallback Fee Denominating Token ID = None",
                    "   Fee Collector Account ID = None",
                    "   All Collectors Are Exempt = True",
                ])
            ),
            (
                CustomRoyaltyFee(
                    numerator=7,
                    denominator=100,
                    fallback_fee=CustomFixedFee(
                        amount=30,
                        denominating_token_id=TokenId(0, 0, 123),
                    ),
                    fee_collector_account_id=AccountId(0, 0, 456),
                    all_collectors_are_exempt=False,
                ),
                "\n".join([
                    "CustomRoyaltyFee:",
                    "   Numerator = 7",
                    "   Denominator = 100",
                    "   Fallback Fee Amount = 30",
                    "   Fallback Fee Denominating Token ID = 0.0.123",
                    "   Fee Collector Account ID = 0.0.456",
                    "   All Collectors Are Exempt = False",
                ])
            )
        ]
)
def test_custom_royalty_fee_str(custom_royalty_fee: CustomRoyaltyFee, expected_str: str):
    """Test the string representation of CustomRoyaltyFee."""
    fee_str = str(custom_royalty_fee)
    assert fee_str == expected_str

class DummyCustomFee(CustomFee):
    def _to_proto(self):
        return "dummy-proto"

def test_custom_fee_init_and_setters():
    fee = DummyCustomFee()
    assert fee.fee_collector_account_id is None
    assert fee.all_collectors_are_exempt is False

    mock_account = AccountId(0, 0, 123)
    fee.set_fee_collector_account_id(mock_account)
    assert fee.fee_collector_account_id == mock_account

    fee.set_all_collectors_are_exempt(True)
    assert fee.all_collectors_are_exempt is True

def test_custom_fee_equality():
    fee1 = DummyCustomFee()
    fee2 = DummyCustomFee()
    assert fee1 == fee2

    fee1.set_all_collectors_are_exempt(True)
    assert fee1 != fee2

def test_custom_fee_get_fee_collector_account_id_protobuf():
    fee = DummyCustomFee()
    assert fee._get_fee_collector_account_id_protobuf() is None

    mock_account = mock.Mock(AccountId)
    mock_account._to_proto.return_value = "proto-account"
    fee.set_fee_collector_account_id(mock_account)
    assert fee._get_fee_collector_account_id_protobuf() == "proto-account"

def test_custom_fee_validate_checksums():
    fee = DummyCustomFee()
    # No account, should not call validate_checksum
    client = mock.Mock(Client)
    fee._validate_checksums(client)

    mock_account = mock.Mock(AccountId)
    fee.set_fee_collector_account_id(mock_account)
    fee._validate_checksums(client)
    mock_account.validate_checksum.assert_called_once_with(client)

def test_custom_fee_from_proto_unrecognized():
    class FakeProto:
        def WhichOneof(self, name):
            return "unknown_fee"
    with pytest.raises(ValueError):
        CustomFee._from_proto(FakeProto())

def test_set_amount_in_tinybars_deprecation():
    """Test that set_amount_in_tinybars shows deprecation warning."""
    fee = CustomFixedFee()
    
    # Test that deprecation warning is raised
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        fee.set_amount_in_tinybars(100)
        
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "set_amount_in_tinybars() is deprecated" in str(w[0].message)
    
    # Verify the method still works correctly
    assert fee.amount == 100
    assert fee.denominating_token_id is None
