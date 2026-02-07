import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.custom_fees_pb2 import AssessedCustomFee as AssessedCustomFeeProto
from hiero_sdk_python.tokens.assessed_custom_fee import AssessedCustomFee
from hiero_sdk_python.tokens.token_id import TokenId


pytestmark = pytest.mark.unit


# If conftest.py has fixtures like sample_account_id or sample_token_id, use them.
# Otherwise, define simple ones here (adjust shard/realm/num as needed for realism).
@pytest.fixture
def sample_account_id() -> AccountId:
    return AccountId(shard=0, realm=0, num=123456)


@pytest.fixture
def sample_token_id() -> TokenId:
    return TokenId(shard=0, realm=0, num=789012)


@pytest.fixture
def another_account_id() -> AccountId:
    return AccountId(shard=0, realm=0, num=999999)


def test_constructor_all_fields(
    sample_account_id: AccountId,
    sample_token_id: TokenId,
    another_account_id: AccountId,
):
    payers = [sample_account_id, another_account_id]
    fee = AssessedCustomFee(
        amount=1_500_000_000,
        token_id=sample_token_id,
        fee_collector_account_id=sample_account_id,
        effective_payer_account_ids=payers,
    )
    assert fee.amount == 1_500_000_000
    assert fee.token_id == sample_token_id
    assert fee.fee_collector_account_id == sample_account_id
    assert fee.effective_payer_account_ids == payers
    # Protect against breaking changes
    assert hasattr(fee, 'amount')
    assert hasattr(fee, 'token_id')
    assert hasattr(fee, 'fee_collector_account_id')
    assert hasattr(fee, 'effective_payer_account_ids')


def test_constructor_hbar_case(sample_account_id: AccountId):
    fee = AssessedCustomFee(
        amount=100_000_000,
        token_id=None,
        fee_collector_account_id=sample_account_id,
    )
    assert fee.amount == 100_000_000
    assert fee.token_id is None
    assert fee.fee_collector_account_id == sample_account_id
    assert fee.effective_payer_account_ids == []


def test_constructor_empty_payers(sample_account_id: AccountId, sample_token_id: TokenId):
    fee = AssessedCustomFee(
        amount=420,
        token_id=sample_token_id,
        fee_collector_account_id=sample_account_id,
        effective_payer_account_ids=[],
    )
    assert fee.effective_payer_account_ids == []
    assert fee.token_id == sample_token_id

def test_constructor_missing_fee_collector_raises():
    """Verify that omitting fee_collector_account_id raises ValueError."""
    with pytest.raises(ValueError, match="fee_collector_account_id is required"):
        AssessedCustomFee(
            amount=100,
            token_id=None,
            fee_collector_account_id=None,
        )

def test_from_proto_missing_token_id(sample_account_id: AccountId):
    """Verify that absence of token_id in protobuf correctly maps to None."""
    proto = AssessedCustomFeeProto(
        amount=750_000,
        fee_collector_account_id=sample_account_id._to_proto(),
        # intentionally no token_id → proto.HasField("token_id") should be False
    )

    fee = AssessedCustomFee._from_proto(proto)

    assert fee.amount == 750_000
    assert fee.token_id is None, "token_id should be None when not present in proto"
    assert fee.fee_collector_account_id == sample_account_id
    assert fee.effective_payer_account_ids == [], "effective payers should default to empty list"

def test_from_proto_with_token_id(sample_account_id: AccountId, sample_token_id: TokenId):
    """Verify that token_id is correctly deserialized when present in proto."""
    proto = AssessedCustomFeeProto(
        amount=500_000,
        token_id=sample_token_id._to_proto(),
        fee_collector_account_id=sample_account_id._to_proto(),
    )
    proto.effective_payer_account_id.append(sample_account_id._to_proto())

    fee = AssessedCustomFee._from_proto(proto)

    assert fee.amount == 500_000
    assert fee.token_id is not None
    assert fee.token_id == sample_token_id
    assert fee.fee_collector_account_id == sample_account_id
    assert len(fee.effective_payer_account_ids) == 1

def test_from_proto_missing_fee_collector_raises():
    """Verify that missing fee_collector_account_id in proto raises ValueError."""
    proto = AssessedCustomFeeProto(amount=750_000)
    with pytest.raises(ValueError, match="fee_collector_account_id is required"):
        AssessedCustomFee._from_proto(proto)

def test_to_proto_basic_fields(
    sample_account_id: AccountId,
    sample_token_id: TokenId,
    another_account_id: AccountId,
):
    """Verify that all basic fields are correctly serialized to protobuf."""
    payers = [sample_account_id, another_account_id]

    fee = AssessedCustomFee(
        amount=2_000_000,
        token_id=sample_token_id,
        fee_collector_account_id=sample_account_id,
        effective_payer_account_ids=payers,
    )

    proto = fee._to_proto()

    # Core presence and value checks
    assert proto.amount == 2_000_000
    assert proto.HasField("token_id"), "token_id should be set when present"
    assert proto.HasField("fee_collector_account_id")
    assert len(proto.effective_payer_account_id) == 2, "should serialize both effective payers"

    # Deeper structural checks (helps catch broken _to_proto implementations)
    assert proto.token_id.shardNum == sample_token_id.shard
    assert proto.token_id.realmNum == sample_token_id.realm
    assert proto.token_id.tokenNum == sample_token_id.num

    # Optional: verify collector (often useful when debugging)
    assert proto.fee_collector_account_id.shardNum == sample_account_id.shard
    assert proto.fee_collector_account_id.realmNum == sample_account_id.realm
    assert proto.fee_collector_account_id.accountNum == sample_account_id.num


def test_round_trip_conversion(
    sample_account_id: AccountId,
    sample_token_id: TokenId,
):
    original = AssessedCustomFee(
        amount=987_654_321,
        token_id=sample_token_id,
        fee_collector_account_id=sample_account_id,
        effective_payer_account_ids=[sample_account_id],
    )

    proto = original._to_proto()
    reconstructed = AssessedCustomFee._from_proto(proto)

    assert reconstructed.amount == original.amount
    assert reconstructed.token_id == original.token_id
    assert reconstructed.fee_collector_account_id == original.fee_collector_account_id
    assert reconstructed.effective_payer_account_ids == original.effective_payer_account_ids


def test_str_contains_expected_fields(
    sample_account_id: AccountId,
    sample_token_id: TokenId,
):
    fee = AssessedCustomFee(
        amount=5_000_000,
        token_id=sample_token_id,
        fee_collector_account_id=sample_account_id,
        effective_payer_account_ids=[sample_account_id],
    )

    s = str(fee)
    assert "AssessedCustomFee" in s
    assert "amount=5000000" in s
    assert str(sample_token_id) in s
    assert str(sample_account_id) in s
    assert "effective_payer_account_ids" in s

    # HBAR case
    hbar_fee = AssessedCustomFee(
        amount=123_456,
        fee_collector_account_id=sample_account_id,
    )
    hbar_str = str(hbar_fee)
    assert "token_id=None" in hbar_str
