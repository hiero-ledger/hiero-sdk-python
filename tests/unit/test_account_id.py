"""
Unit tests for the AccountId class.
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services import basic_types_pb2

pytestmark = pytest.mark.unit


@pytest.fixture
def alias_key():
    """Returns an Ed25519 alias key."""
    return PrivateKey.generate_ed25519().public_key()


@pytest.fixture
def alias_key2():
    """Returns an Ed25519 alias key."""
    return PrivateKey.generate_ed25519().public_key()


@pytest.fixture
def alias_key_ecdsa():
    """Returns an ECDSA alias key."""
    return PrivateKey.generate_ecdsa().public_key()


@pytest.fixture
def account_id_100():
    """AccountId with num=100 for testing."""
    return AccountId(shard=0, realm=0, num=100)

@pytest.fixture
def account_id_101():
    """AccountId with num=101 for testing."""
    return AccountId(shard=0, realm=0, num=101)

@pytest.fixture
def client(mock_client):
    mock_client.network.ledger_id = bytes.fromhex("00") # Mainnet ledger id
    return mock_client

def test_default_initialization():
    """Test AccountId initialization with default values."""
    account_id = AccountId()

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key is None
    assert account_id.checksum is None


def test_custom_initialization(account_id_100):
    """Test AccountId initialization with custom values."""
    assert account_id_100.shard == 0
    assert account_id_100.realm == 0
    assert account_id_100.num == 100
    assert account_id_100.alias_key is None
    assert account_id_100.checksum is None


def test_initialization_with_alias_key(alias_key):
    """Test AccountId initialization with alias key."""
    account_id = AccountId(shard=0, realm=0, num=0, alias_key=alias_key)

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key == alias_key
    assert account_id.checksum is None


def test_str_representation(account_id_100):
    """Test string representation of AccountId without alias key."""
    assert str(account_id_100) == "0.0.100"


def test_str_representation_default(account_id_100):
    """Test string representation of AccountId with default values."""
    assert str(account_id_100) == "0.0.100"


def test_str_representation_with_checksum(client, account_id_100):
    """Test string representation of AccountId with checksum."""
    assert account_id_100.to_string_with_checksum(client) == "0.0.100-hhghj"


def test_str_representation_with_checksum_if_alias_key_present(client, account_id_100, alias_key):
    """AccountId with aliasKey should raise ValueError on to_string_with_checksum"""
    account_id = account_id_100
    account_id.alias_key = alias_key

    with pytest.raises(ValueError, match="Cannot calculate checksum with an account ID that has a aliasKey"):
        account_id.to_string_with_checksum(client)


def test_str_representation_with_alias_key(alias_key):
    """Test string representation of AccountId with alias key."""
    account_id = AccountId(shard=0, realm=0, num=0, alias_key=alias_key)

    # Should use alias key string representation instead of num
    expected = f"0.0.{alias_key.to_string()}"
    assert str(account_id) == expected


def test_repr_representation(account_id_100):
    """Test repr representation of AccountId without alias key."""
    assert repr(account_id_100) == "AccountId(shard=0, realm=0, num=100)"


def test_repr_representation_with_alias_key(alias_key):
    """Test repr representation of AccountId with alias key."""
    account_id = AccountId(shard=0, realm=0, num=0, alias_key=alias_key)

    expected = f"AccountId(shard=0, realm=0, alias_key={alias_key.to_string_raw()})"
    assert repr(account_id) == expected


def test_from_string_valid():
    """Test creating AccountId from valid string format."""
    account_id = AccountId.from_string("0.0.100")

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 100
    assert account_id.alias_key is None
    assert account_id.checksum is None


def test_from_string_zeros():
    """Test creating AccountId from string with zero values."""
    account_id = AccountId.from_string("0.0.100")

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 100
    assert account_id.alias_key is None
    assert account_id.checksum is None


def test_from_string_with_checksum():
    """Test creating AccountId from string with zero values."""
    account_id = AccountId.from_string("0.0.100-abcde")

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 100
    assert account_id.alias_key is None
    assert account_id.checksum == 'abcde'


def test_from_string_with_alias_key(alias_key):
    account_id_str = f"0.0.{alias_key.to_string()}"
    account_id = AccountId.from_string(account_id_str)

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key.__eq__(alias_key)
    assert account_id.checksum is None

def test_from_string_with_alias_key_ecdsa(alias_key_ecdsa):
    account_id_str = f"0.0.{alias_key_ecdsa.to_string()}"
    account_id = AccountId.from_string(account_id_str)

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key.__eq__(alias_key_ecdsa)
    assert account_id.checksum is None


@pytest.mark.parametrize(
    'invalid_id', 
    [
        '1.2',  # Too few parts
        '1.2.3.4',  # Too many parts
        'a.b.c',  # Non-numeric parts
        '',  # Empty string
        '1.a.3',  # Partial numeric
        123,
        None,
        '0.0.-1',
        'abc.def.ghi',
        '0.0.1-ad',
        '0.0.1-addefgh',
        '0.0.1 - abcde',
        ' 0.0.100 ',
        '0.0.302a300506032b6570032100114e6abc371b82dab5c15ea149f02d34a012087b163516dd70f44acafabf777g',
        '0.0.302a300506032b6570032100114e6abc371b82dab5c15ea149f02d34a012087b163516dd70f44acafabf777'
    ]
)
def test_from_string_for_invalid_format(invalid_id):
    """Should raise error when creating AccountId from invalid string input."""
    with pytest.raises(
        ValueError, match=f"Invalid account ID string '{invalid_id}'. Expected format 'shard.realm.num'."
    ):
        AccountId.from_string(invalid_id)


def test_to_proto(account_id_100):
    """Test converting AccountId to protobuf format."""
    proto = account_id_100._to_proto()

    assert isinstance(proto, basic_types_pb2.AccountID)
    assert proto.shardNum == 0
    assert proto.realmNum == 0
    assert proto.accountNum == 100
    assert proto.alias == b""


def test_to_proto_default_values():
    """Test converting AccountId with default values to protobuf format."""
    proto = AccountId()._to_proto()

    assert isinstance(proto, basic_types_pb2.AccountID)
    assert proto.shardNum == 0
    assert proto.realmNum == 0
    assert proto.accountNum == 0
    assert proto.alias == b""


def test_to_proto_with_alias_key(alias_key):
    """Test converting AccountId with Ed25519 alias key to protobuf format."""
    account_id = AccountId(shard=0, realm=0, num=100, alias_key=alias_key)
    proto = account_id._to_proto()

    assert isinstance(proto, basic_types_pb2.AccountID)
    assert proto.shardNum == 0
    assert proto.realmNum == 0
    assert proto.accountNum == 0
    assert proto.alias == alias_key._to_proto().SerializeToString()


def test_to_proto_with_ecdsa_alias_key(alias_key_ecdsa):
    """Test converting AccountId with ECDSA alias key to protobuf format."""
    account_id = AccountId(shard=0, realm=0, num=100, alias_key=alias_key_ecdsa)
    proto = account_id._to_proto()

    assert isinstance(proto, basic_types_pb2.AccountID)
    assert proto.shardNum == 0
    assert proto.realmNum == 0
    assert proto.accountNum == 0
    assert proto.alias == alias_key_ecdsa._to_proto().SerializeToString()


def test_from_proto():
    """Test creating AccountId from protobuf format."""
    proto = basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=100)

    account_id = AccountId._from_proto(proto)

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 100
    assert account_id.alias_key is None


def test_from_proto_zero_values():
    """Test creating AccountId from protobuf format with zero values."""
    proto = basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=0)

    account_id = AccountId._from_proto(proto)

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key is None


def test_from_proto_with_alias(alias_key):
    """Test creating AccountId from protobuf format with Ed25519 alias."""
    proto = basic_types_pb2.AccountID(
        shardNum=0,
        realmNum=0,
        accountNum=3,
        alias=alias_key._to_proto().SerializeToString(),
    )

    account_id = AccountId._from_proto(proto)
    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key is not None
    # Compare the raw bytes
    assert account_id.alias_key.to_bytes_raw() == alias_key.to_bytes_raw()


def test_from_proto_with_ecdsa_alias(alias_key_ecdsa):
    """Test creating AccountId from protobuf format with ECDSA alias."""
    proto = basic_types_pb2.AccountID(
        shardNum=0,
        realmNum=0,
        accountNum=3,
        alias=alias_key_ecdsa._to_proto().SerializeToString(),
    )

    account_id = AccountId._from_proto(proto)
    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key is not None
    # Compare the raw bytes
    assert account_id.alias_key.to_bytes_raw() == alias_key_ecdsa.to_bytes_raw()


def test_roundtrip_proto_conversion(account_id_100):
    """Test that converting to proto and back preserves values."""
    proto = account_id_100._to_proto()
    reconstructed = AccountId._from_proto(proto)

    assert account_id_100.shard == reconstructed.shard
    assert account_id_100.realm == reconstructed.realm
    assert account_id_100.num == reconstructed.num
    assert account_id_100.alias_key == reconstructed.alias_key


def test_roundtrip_proto_conversion_with_alias(alias_key):
    """Test that converting to proto and back preserves values including Ed25519 alias."""
    original = AccountId(shard=0, realm=0, num=0, alias_key=alias_key)
    proto = original._to_proto()
    reconstructed = AccountId._from_proto(proto)

    assert original.shard == reconstructed.shard
    assert original.realm == reconstructed.realm
    assert original.num == reconstructed.num
    assert original.alias_key is not None
    assert reconstructed.alias_key is not None
    # Compare the raw bytes
    assert original.alias_key.to_bytes_raw() == reconstructed.alias_key.to_bytes_raw()


def test_roundtrip_proto_conversion_with_ecdsa_alias(alias_key_ecdsa):
    """Test that converting to proto and back preserves values including ECDSA alias."""
    original = AccountId(shard=0, realm=0, num=0, alias_key=alias_key_ecdsa)
    proto = original._to_proto()
    reconstructed = AccountId._from_proto(proto)

    assert original.shard == reconstructed.shard
    assert original.realm == reconstructed.realm
    assert original.num == reconstructed.num
    assert original.alias_key is not None
    assert reconstructed.alias_key is not None
    # Compare the raw bytes
    assert original.alias_key.to_bytes_raw() == reconstructed.alias_key.to_bytes_raw()


def test_roundtrip_string_conversion(account_id_100):
    """Test that converting to string and back preserves values."""
    string_repr = str(account_id_100)
    reconstructed = AccountId.from_string(string_repr)

    assert account_id_100.shard == reconstructed.shard
    assert account_id_100.realm == reconstructed.realm
    assert account_id_100.num == reconstructed.num
    assert account_id_100.alias_key == reconstructed.alias_key


def test_equality(account_id_100, account_id_101):
    """Test AccountId equality comparison."""
    account_id2 = AccountId(shard=0, realm=0, num=100)

    assert account_id_100 == account_id2
    assert account_id_100 != account_id_101


def test_equality_with_alias_key(alias_key, alias_key2):
    """Test AccountId equality comparison with alias keys."""
    account_id1 = AccountId(shard=0, realm=0, num=0, alias_key=alias_key)
    account_id2 = AccountId(shard=0, realm=0, num=0, alias_key=alias_key)
    account_id3 = AccountId(shard=0, realm=0, num=0, alias_key=alias_key2)
    account_id4 = AccountId(shard=0, realm=0, num=0, alias_key=None)

    # Same alias key should be equal
    assert account_id1 == account_id2

    # Different alias keys should not be equal
    assert account_id1 != account_id3

    # None alias key should not be equal to one with alias key
    assert account_id1 != account_id4


def test_equality_different_types(account_id_100):
    """Test AccountId equality with different types."""
    assert account_id_100 != "1.2.3"
    assert account_id_100 != 123
    assert account_id_100 != None


def test_hash(account_id_100, account_id_101):
    """Test AccountId hash function."""
    account_id2 = AccountId(shard=0, realm=0, num=100)

    # Same values should have same hash
    assert hash(account_id_100) == hash(account_id2)

    # Different values should have different hashes
    assert hash(account_id_100) != hash(account_id_101)


def test_hash_with_alias_key(alias_key, alias_key2):
    """Test AccountId hash with alias keys."""
    account_id1 = AccountId(shard=0, realm=0, num=0, alias_key=alias_key)
    account_id2 = AccountId(shard=0, realm=0, num=0, alias_key=alias_key)
    account_id3 = AccountId(shard=0, realm=0, num=0, alias_key=alias_key2)

    # Same alias key should have same hash
    assert hash(account_id1) == hash(account_id2)

    # Different alias keys should have different hashes
    assert hash(account_id1) != hash(account_id3)


def test_alias_key_affects_proto_serialization(account_id_100, alias_key):
    """Test that alias key affects protobuf serialization correctly."""
    # Without alias key
    proto_no_alias = account_id_100._to_proto()
    assert proto_no_alias.accountNum == 100
    assert proto_no_alias.alias == b""

    # With alias key
    account_id_with_alias = AccountId(shard=0, realm=0, num=0, alias_key=alias_key)
    proto_with_alias = account_id_with_alias._to_proto()
    assert proto_with_alias.accountNum == 0
    assert proto_with_alias.alias == alias_key._to_proto().SerializeToString()


def test_alias_key_deserialization_from_proto(alias_key):
    """Test that alias key is correctly deserialized from protobuf."""
    # Create proto with alias
    proto = basic_types_pb2.AccountID(
        shardNum=0,
        realmNum=0,
        accountNum=0,
        alias=alias_key._to_proto().SerializeToString(),
    )

    account_id = AccountId._from_proto(proto)

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key is not None
    assert account_id.alias_key.to_bytes_raw() == alias_key.to_bytes_raw()


def test_alias_key_deserialization_from_empty_proto():
    """Test that empty alias in proto results in None alias_key."""
    proto = basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=100, alias=b"")

    account_id = AccountId._from_proto(proto)

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key is None


def test_alias_key_affects_string_representation(alias_key, alias_key2, account_id_100):
    """Test that alias key changes string representation behavior."""
    # Same shard/realm/num but different alias keys should have different string representations
    account_id1 = AccountId(shard=0, realm=0, num=0, alias_key=alias_key)
    account_id2 = AccountId(shard=0, realm=0, num=0, alias_key=alias_key2)

    str1 = str(account_id1)
    str2 = str(account_id2)
    str3 = str(account_id_100)

    # All should have different string representations
    assert str1 != str2
    assert str1 != str3
    assert str2 != str3

    # Account with alias should include alias key string
    assert alias_key.to_string() in str1
    assert alias_key2.to_string() in str2

    # Account without alias should use num
    assert str3 == "0.0.100"

def test_validate_checksum_for_id(client):
    """Test validateChecksum for accountId"""
    account_id = AccountId.from_string("0.0.100-hhghj")
    account_id.validate_checksum(client)


def test_validate_checksum_with_alias_key_set(client, alias_key):
    """Test validateChecksum should raise ValueError if aliasKey is set"""
    account_id = AccountId.from_string("0.0.100-hhghj")
    account_id.alias_key = alias_key

    with pytest.raises(ValueError, match="Cannot calculate checksum with an account ID that has a aliasKey"):
        account_id.validate_checksum(client)


def test_validate_checksum_for_invalid_checksum(client):
    """Test Invalid Checksum for Id should raise ValueError"""
    account_id = AccountId.from_string("0.0.100-abcde")
    
    with pytest.raises(ValueError, match="Checksum mismatch for 0.0.100"):
        account_id.validate_checksum(client)
