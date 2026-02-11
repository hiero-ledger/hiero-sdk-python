import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_association import TokenAssociation
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenAssociation as TokenAssociationProto


pytestmark = pytest.mark.unit


# ────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_token_id() -> TokenId:
    return TokenId(shard=0, realm=0, num=123456)


@pytest.fixture
def sample_account_id() -> AccountId:
    return AccountId(shard=0, realm=0, num=789012)


# ────────────────────────────────────────────────────────────────
# Constructor / Initialization Tests
# ────────────────────────────────────────────────────────────────

def test_default_initialization():
    assoc = TokenAssociation()
    assert assoc.token_id is None
    assert assoc.account_id is None


def test_initialization_with_values(sample_token_id, sample_account_id):
    assoc = TokenAssociation(
        token_id=sample_token_id,
        account_id=sample_account_id,
    )
    assert assoc.token_id == sample_token_id
    assert assoc.account_id == sample_account_id


def test_initialization_partial(sample_token_id):
    assoc = TokenAssociation(token_id=sample_token_id)
    assert assoc.token_id == sample_token_id
    assert assoc.account_id is None

    assoc2 = TokenAssociation(account_id=sample_account_id)
    assert assoc2.token_id is None
    assert assoc2.account_id == sample_account_id


# ────────────────────────────────────────────────────────────────
# _from_proto Tests
# ────────────────────────────────────────────────────────────────

def test_from_proto_full(sample_token_id, sample_account_id):
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


def test_from_proto_missing_token_id(sample_account_id):
    proto = TokenAssociationProto()
    proto.account_id.shardNum = sample_account_id.shard
    proto.account_id.realmNum = sample_account_id.realm
    proto.account_id.accountNum = sample_account_id.num

    assoc = TokenAssociation._from_proto(proto)

    assert assoc.token_id is None
    assert assoc.account_id == sample_account_id


def test_from_proto_missing_account_id(sample_token_id):
    proto = TokenAssociationProto()
    proto.token_id.shardNum = sample_token_id.shard
    proto.token_id.realmNum = sample_token_id.realm
    proto.token_id.tokenNum = sample_token_id.num

    assoc = TokenAssociation._from_proto(proto)

    assert assoc.token_id == sample_token_id
    assert assoc.account_id is None


def test_from_proto_empty():
    proto = TokenAssociationProto()
    assoc = TokenAssociation._from_proto(proto)
    assert assoc.token_id is None
    assert assoc.account_id is None


# ────────────────────────────────────────────────────────────────
# _to_proto Tests
# ────────────────────────────────────────────────────────────────

def test_to_proto_full(sample_token_id, sample_account_id):
    assoc = TokenAssociation(
        token_id=sample_token_id,
        account_id=sample_account_id,
    )

    proto = assoc._to_proto()

    assert proto.HasField("token_id")
    assert proto.token_id.tokenNum == sample_token_id.num
    assert proto.HasField("account_id")
    assert proto.account_id.accountNum == sample_account_id.num


def test_to_proto_partial(sample_token_id):
    assoc = TokenAssociation(token_id=sample_token_id)
    proto = assoc._to_proto()

    assert proto.HasField("token_id")
    assert proto.token_id.tokenNum == sample_token_id.num
    assert not proto.HasField("account_id")


def test_to_proto_empty():
    assoc = TokenAssociation()
    proto = assoc._to_proto()

    assert not proto.HasField("token_id")
    assert not proto.HasField("account_id")


# ────────────────────────────────────────────────────────────────
# Round-trip Tests
# ────────────────────────────────────────────────────────────────

def test_round_trip_full(sample_token_id, sample_account_id):
    original = TokenAssociation(
        token_id=sample_token_id,
        account_id=sample_account_id,
    )

    proto = original._to_proto()
    reconstructed = TokenAssociation._from_proto(proto)

    assert reconstructed == original  # works because dataclass(frozen=True) has __eq__


def test_round_trip_empty():
    original = TokenAssociation()
    proto = original._to_proto()
    reconstructed = TokenAssociation._from_proto(proto)

    assert reconstructed.token_id is None
    assert reconstructed.account_id is None


def test_round_trip_partial_token_only(sample_token_id):
    original = TokenAssociation(token_id=sample_token_id)
    proto = original._to_proto()
    reconstructed = TokenAssociation._from_proto(proto)

    assert reconstructed.token_id == sample_token_id
    assert reconstructed.account_id is None


def test_round_trip_partial_account_only(sample_account_id):
    original = TokenAssociation(account_id=sample_account_id)
    proto = original._to_proto()
    reconstructed = TokenAssociation._from_proto(proto)

    assert reconstructed.token_id is None
    assert reconstructed.account_id == sample_account_id


# ────────────────────────────────────────────────────────────────
# String / Repr Tests
# ────────────────────────────────────────────────────────────────

def test_str_and_repr(sample_token_id, sample_account_id):
    assoc = TokenAssociation(
        token_id=sample_token_id,
        account_id=sample_account_id,
    )

    s = str(assoc)
    r = repr(assoc)

    assert "TokenAssociation" in s
    assert str(sample_token_id) in s
    assert str(sample_account_id) in s

    assert s == r  # since __repr__ delegates to __str__
