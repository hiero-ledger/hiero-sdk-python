import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenAssociation as TokenAssociationProto
from hiero_sdk_python.tokens.token_association import TokenAssociation
from hiero_sdk_python.tokens.token_id import TokenId


pytestmark = pytest.mark.unit


@pytest.fixture
def sample_token_id() -> TokenId:
    return TokenId(shard=0, realm=0, num=5678)


@pytest.fixture
def sample_account_id() -> AccountId:
    return AccountId(shard=0, realm=0, num=1234)


def test_default_initialization():
    """Test default initialization of TokenAssociation (both fields None)."""
    assoc = TokenAssociation()

    assert assoc.token_id is None
    assert assoc.account_id is None


def test_initialization_both_fields(sample_token_id: TokenId, sample_account_id: AccountId):
    """Test initialization with both token_id and account_id provided."""
    assoc = TokenAssociation(
        token_id=sample_token_id,
        account_id=sample_account_id
    )

    assert assoc.token_id == sample_token_id
    assert assoc.account_id == sample_account_id


def test_initialization_token_only(sample_token_id: TokenId):
    """Test initialization with only token_id (account_id None)."""
    assoc = TokenAssociation(token_id=sample_token_id)

    assert assoc.token_id == sample_token_id
    assert assoc.account_id is None


def test_initialization_account_only(sample_account_id: AccountId):
    """Test initialization with only account_id (token_id None)."""
    assoc = TokenAssociation(account_id=sample_account_id)

    assert assoc.token_id is None
    assert assoc.account_id == sample_account_id


def test_from_proto_both_fields(sample_token_id: TokenId, sample_account_id: AccountId):
    """Test _from_proto with both token_id and account_id present in proto."""
    proto = TokenAssociationProto()
    proto.token_id.shardNum = sample_token_id.shard
    proto.token_id.realmNum = sample_token_id.realm
    proto.token_id.tokenNum = sample_token_id.num
    proto.account_id.shardNum = sample_account_id.shard
    proto.account_id.realmNum = sample_account_id.realm
    proto.account_id.accountNum = sample_account_id.num

    assoc = TokenAssociation._from_proto(proto)

    assert assoc.token_id == sample_token_id
    assert assoc.account_id == sample_account_id


def test_from_proto_token_only(sample_token_id: TokenId):
    """Test _from_proto with only token_id present (account_id absent)."""
    proto = TokenAssociationProto()
    proto.token_id.shardNum = sample_token_id.shard
    proto.token_id.realmNum = sample_token_id.realm
    proto.token_id.tokenNum = sample_token_id.num

    assoc = TokenAssociation._from_proto(proto)

    assert assoc.token_id == sample_token_id
    assert assoc.account_id is None


def test_from_proto_account_only(sample_account_id: AccountId):
    """Test _from_proto with only account_id present (token_id absent)."""
    proto = TokenAssociationProto()
    proto.account_id.shardNum = sample_account_id.shard
    proto.account_id.realmNum = sample_account_id.realm
    proto.account_id.accountNum = sample_account_id.num

    assoc = TokenAssociation._from_proto(proto)

    assert assoc.token_id is None
    assert assoc.account_id == sample_account_id


def test_from_proto_empty():
    """Test _from_proto with completely empty protobuf message."""
    proto = TokenAssociationProto()
    assoc = TokenAssociation._from_proto(proto)

    assert assoc.token_id is None
    assert assoc.account_id is None


def test_to_proto_both_fields(sample_token_id: TokenId, sample_account_id: AccountId):
    """Test _to_proto serializes both fields correctly."""
    assoc = TokenAssociation(
        token_id=sample_token_id,
        account_id=sample_account_id
    )

    proto = assoc._to_proto()

    assert proto.HasField("token_id")
    assert proto.token_id.shardNum == sample_token_id.shard
    assert proto.token_id.realmNum == sample_token_id.realm
    assert proto.token_id.tokenNum == sample_token_id.num

    assert proto.HasField("account_id")
    assert proto.account_id.shardNum == sample_account_id.shard
    assert proto.account_id.realmNum == sample_account_id.realm
    assert proto.account_id.accountNum == sample_account_id.num


def test_to_proto_token_only(sample_token_id: TokenId):
    """Test _to_proto with only token_id (account_id None)."""
    assoc = TokenAssociation(token_id=sample_token_id)
    proto = assoc._to_proto()

    assert proto.HasField("token_id")
    assert not proto.HasField("account_id")


def test_to_proto_account_only(sample_account_id: AccountId):
    """Test _to_proto with only account_id (token_id None)."""
    assoc = TokenAssociation(account_id=sample_account_id)
    proto = assoc._to_proto()

    assert not proto.HasField("token_id")
    assert proto.HasField("account_id")


def test_to_proto_empty():
    """Test _to_proto with empty/default instance."""
    assoc = TokenAssociation()
    proto = assoc._to_proto()

    assert not proto.HasField("token_id")
    assert not proto.HasField("account_id")


def test_round_trip_both_fields(sample_token_id: TokenId, sample_account_id: AccountId):
    """Test full round-trip conversion preserves both fields."""
    original = TokenAssociation(
        token_id=sample_token_id,
        account_id=sample_account_id
    )

    proto = original._to_proto()
    reconstructed = TokenAssociation._from_proto(proto)

    assert reconstructed.token_id == original.token_id
    assert reconstructed.account_id == original.account_id


def test_round_trip_token_only(sample_token_id: TokenId):
    """Test round-trip with only token_id."""
    original = TokenAssociation(token_id=sample_token_id)
    proto = original._to_proto()
    reconstructed = TokenAssociation._from_proto(proto)

    assert reconstructed.token_id == original.token_id
    assert reconstructed.account_id is None


def test_round_trip_account_only(sample_account_id: AccountId):
    """Test round-trip with only account_id."""
    original = TokenAssociation(account_id=sample_account_id)
    proto = original._to_proto()
    reconstructed = TokenAssociation._from_proto(proto)

    assert reconstructed.token_id is None
    assert reconstructed.account_id == original.account_id


def test_round_trip_empty():
    """Test round-trip with empty/default instance."""
    original = TokenAssociation()
    proto = original._to_proto()
    reconstructed = TokenAssociation._from_proto(proto)

    assert reconstructed.token_id is None
    assert reconstructed.account_id is None


def test_str_representation(sample_token_id: TokenId, sample_account_id: AccountId):
    """Test that __str__ contains expected field information."""
    assoc = TokenAssociation(
        token_id=sample_token_id,
        account_id=sample_account_id
    )
    s = str(assoc)
    assert "TokenAssociation" in s
    assert str(sample_token_id) in s
    assert str(sample_account_id) in s


def test_str_with_none_fields():
    """Test __str__ with one or both fields None."""
    assoc_token_only = TokenAssociation(token_id=TokenId(shard=0, realm=0, num=5678))
    s_token = str(assoc_token_only)
    assert "token_id=0.0.5678" in s_token
    assert "account_id=None" in s_token

    assoc_account_only = TokenAssociation(account_id=AccountId(shard=0, realm=0, num=1234))
    s_account = str(assoc_account_only)
    assert "token_id=None" in s_account
    assert "account_id=0.0.1234" in s_account

    assoc_empty = TokenAssociation()
    s_empty = str(assoc_empty)
    assert "token_id=None" in s_empty
    assert "account_id=None" in s_empty