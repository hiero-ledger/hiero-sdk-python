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


def test_from_proto_missing_token_id(sample_account_id: AccountId):
    proto = AssessedCustomFeeProto(
        amount=750_000,
        fee_collector_account_id=sample_account_id._to_proto(),
        # no token_id set → HasField("token_id") == False
    )
    fee = AssessedCustomFee._from_proto(proto)
    assert fee.amount == 750_000
    assert fee.token_id is None
    assert fee.fee_collector_account_id == sample_account_id
    assert fee.effective_payer_account_ids == []


def test_to_proto_basic_fields(
    sample_account_id: AccountId,
    sample_token_id: TokenId,
    another_account_id: AccountId,
):
    fee = AssessedCustomFee(
        amount=2_000_000,
        token_id=sample_token_id,
        fee_collector_account_id=sample_account_id,
        effective_payer_account_ids=[sample_account_id, another_account_id],
    )

    proto = fee._to_proto()

    assert proto.amount == 2_000_000
    assert proto.HasField("token_id")
    assert proto.HasField("fee_collector_account_id")
    assert len(proto.effective_payer_account_id) == 2

    # Optional: deeper checks if AccountId/TokenId ._to_proto() are reliable
    assert proto.token_id.shardNum == sample_token_id.shard
    assert proto.token_id.realmNum == sample_token_id.realm
    assert proto.token_id.tokenNum == sample_token_id.num


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
    assert "amount=5000000" in s or "amount=5_000_000" in s  # depending on __str__ formatting
    assert str(sample_token_id) in s
    assert str(sample_account_id) in s
    assert "effective_payers" in s or "effective_payer_account_ids" in s
    assert str(sample_account_id) in s  # payer appears

    # HBAR case
    hbar_fee = AssessedCustomFee(
        amount=123_456,
        fee_collector_account_id=sample_account_id,
    )
    hbar_str = str(hbar_fee)
    assert "token_id=None" in hbar_str or "HBAR" in hbar_str