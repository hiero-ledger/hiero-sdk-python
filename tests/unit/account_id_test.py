"""
Unit tests for the AccountId class.
"""

from unittest.mock import MagicMock, patch
import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.evm_address import EvmAddress
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
def evm_address():
    """Returns an EVM Address."""
    return PrivateKey.generate_ecdsa().public_key().to_evm_address()


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
    mock_client.network.ledger_id = bytes.fromhex("00")  # Mainnet ledger id
    return mock_client


def test_default_initialization():
    """Test AccountId initialization with default values."""
    account_id = AccountId()

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key is None
    assert account_id.checksum is None
    assert account_id.evm_address is None


def test_custom_initialization(account_id_100):
    """Test AccountId initialization with custom values."""
    assert account_id_100.shard == 0
    assert account_id_100.realm == 0
    assert account_id_100.num == 100
    assert account_id_100.alias_key is None
    assert account_id_100.checksum is None
    assert account_id_100.evm_address is None


def test_initialization_with_alias_key(alias_key):
    """Test AccountId initialization with alias key."""
    account_id = AccountId(shard=0, realm=0, num=0, alias_key=alias_key)

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key == alias_key
    assert account_id.checksum is None
    assert account_id.evm_address is None


def test_initialization_with_evm_address(evm_address):
    """Test AccountId initialization with evm_address."""
    account_id = AccountId(shard=0, realm=0, num=0, evm_address=evm_address)

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key is None
    assert account_id.checksum is None
    assert account_id.evm_address == evm_address


def test_str_representation(account_id_100):
    """Test string representation of AccountId without alias key."""
    assert str(account_id_100) == "0.0.100"


def test_str_representation_default(account_id_100):
    """Test string representation of AccountId with default values."""
    assert str(account_id_100) == "0.0.100"


def test_str_representation_with_checksum(client, account_id_100):
    """Test string representation of AccountId with checksum."""
    assert account_id_100.to_string_with_checksum(client) == "0.0.100-hhghj"


def test_str_representation_with_checksum_if_alias_key_present(
    client, account_id_100, alias_key
):
    """AccountId with aliasKey should raise ValueError on to_string_with_checksum"""
    account_id = account_id_100
    account_id.alias_key = alias_key

    with pytest.raises(
        ValueError,
        match="Cannot calculate checksum with an account ID that has a aliasKey or evmAddress",
    ):
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


def test_repr_representation_with_evm_address(evm_address):
    """Test repr representation of AccountId with evm_address."""
    account_id = AccountId(shard=0, realm=0, num=0, evm_address=evm_address)

    expected = f"AccountId(shard=0, realm=0, evm_address={evm_address.to_string()})"
    assert repr(account_id) == expected


@pytest.mark.parametrize(
    "account_str, expected",
    [
        ("0.0.100", (0, 0, 100, None, None, None)),
        ("0.0.100-abcde", (0, 0, 100, "abcde", None, None)),
        (
            "302a300506032b6570032100114e6abc371b82da",
            (
                0,
                0,
                0,
                None,
                None,
                EvmAddress.from_string("302a300506032b6570032100114e6abc371b82da"),
            ),
        ),
        (
            "0x302a300506032b6570032100114e6abc371b82da",
            (
                0,
                0,
                0,
                None,
                None,
                EvmAddress.from_string("302a300506032b6570032100114e6abc371b82da"),
            ),
        ),
        (
            "0.0.302a300506032b6570032100114e6abc371b82da",
            (
                0,
                0,
                0,
                None,
                None,
                EvmAddress.from_string("302a300506032b6570032100114e6abc371b82da"),
            ),
        ),
    ],
)
def test_from_string_valid(account_str, expected):
    """Test creating AccountId from valid string format."""
    shard, realm, num, checksum, alias_key, evm_address = expected
    account_id = AccountId.from_string(account_str)

    assert account_id.shard == shard
    assert account_id.realm == realm
    assert account_id.num == num
    assert account_id.checksum == checksum
    assert account_id.alias_key == alias_key
    assert account_id.evm_address == evm_address


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
    assert account_id.checksum == "abcde"


@pytest.mark.parametrize(
    "alias_fixture", ["alias_key", "alias_key_ecdsa", "evm_address"]
)
def test_from_string_with_alias(request, alias_fixture):
    """Test create AccountId from string with different alias."""
    alias = request.getfixturevalue(alias_fixture)

    account_id_str = f"0.0.{alias.to_string()}"
    account_id = AccountId.from_string(account_id_str)

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.checksum is None

    if isinstance(alias, EvmAddress):
        assert account_id.evm_address == alias
        assert account_id.alias_key is None
    else:
        assert account_id.alias_key.__eq__(alias)
        assert account_id.evm_address is None


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("0x1234567890abcdef1234567890abcdef12345678", True),  # valid 0x-prefixed
        ("1234567890abcdef1234567890abcdef12345678", True),  # valid raw
        ("0x123", False),  # too short
        ("1234567890abcdef1234567890abcdef1234567890", False),  # too long
        ("0xZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ", False),  # invalid hex
    ],
)
def test_is_evm_address(input_str, expected):
    """Test _is_evm_address static method for all branches."""
    assert AccountId._is_evm_address(input_str) == expected


@pytest.mark.parametrize(
    "invalid_id",
    [
        "1.2",  # Too few parts
        "1.2.3.4",  # Too many parts
        "a.b.c",  # Non-numeric parts
        "",  # Empty string
        "1.a.3",  # Partial numeric
        "0.0.-1",
        "abc.def.ghi",
        "0.0.1-ad",
        "0.0.1-addefgh",
        "0.0.1 - abcde",
        " 0.0.100 ",
        "0.0.302a300506032b6570032100114e6abc371b82dab5c15ea149f02d34a012087b163516dd70f44acafabf777g",
        "0.0.302a300506032b6570032100114e6abc371b82dab5c15ea149f02d34a012087b163516dd70f44acafabf777",
        "0.0.302a300506032b6570032100114e6abc371b82d",
        "0.0.ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
        "302a300506032b6570032100114e6abc371b82d",
        "0x302a300506032b6570032100114e6abc371b82d",
        "0xZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",  # invalid hex
        "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
    ],
)
def test_from_string_for_invalid_format(invalid_id):
    """Should raise error when creating AccountId from invalid string input."""
    with pytest.raises(
        ValueError,
        match=f"Invalid account ID string '{invalid_id}'."
        "Supported formats: "
        "'shard.realm.num', "
        "'shard.realm.num-checksum', "
        "'shard.realm.<hex-alias>', "
        "or a 20-byte EVM address.",
    ):
        AccountId.from_string(invalid_id)


@pytest.mark.parametrize("invalid_id", [123, None, True, object, {}])
def test_from_string_for_invalid_types(invalid_id):
    """Should raise error when creating AccountId from invalid types."""
    with pytest.raises(
        TypeError,
        match=f"account_id_str must be a string, got {type(invalid_id).__name__}.",
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


def test_to_proto_with_evm_address(evm_address):
    """Test converting AccountId with evm_address to protobuf format."""
    account_id = AccountId(shard=0, realm=0, num=100, evm_address=evm_address)
    proto = account_id._to_proto()

    assert isinstance(proto, basic_types_pb2.AccountID)
    assert proto.shardNum == 0
    assert proto.realmNum == 0
    assert proto.accountNum == 0
    assert proto.alias == evm_address.address_bytes


def test_from_proto():
    """Test creating AccountId from protobuf format."""
    proto = basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=100)

    account_id = AccountId._from_proto(proto)

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 100
    assert account_id.alias_key is None
    assert account_id.evm_address is None


def test_from_proto_zero_values():
    """Test creating AccountId from protobuf format with zero values."""
    proto = basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=0)

    account_id = AccountId._from_proto(proto)

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key is None
    assert account_id.evm_address is None


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
    assert account_id.evm_address is None
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
    assert account_id.evm_address is None
    assert account_id.alias_key is not None
    # Compare the raw bytes
    assert account_id.alias_key.to_bytes_raw() == alias_key_ecdsa.to_bytes_raw()


def test_from_proto_with_evm_address_as_alias(evm_address):
    """Test creating AccountId from protobuf format with evm_address."""
    proto = basic_types_pb2.AccountID(
        shardNum=0,
        realmNum=0,
        accountNum=3,
        alias=evm_address.address_bytes,
    )

    account_id = AccountId._from_proto(proto)
    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key is None
    assert account_id.evm_address is not None
    assert account_id.evm_address == evm_address


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
    assert account_id_100.evm_address == reconstructed.evm_address


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


def test_equality_with_evm_address(evm_address):
    """Test AccountId equality comparison with alias keys."""
    account_id1 = AccountId(shard=0, realm=0, num=0, evm_address=evm_address)
    account_id2 = AccountId(shard=0, realm=0, num=0, evm_address=evm_address)
    account_id3 = AccountId(
        shard=0,
        realm=0,
        num=0,
        evm_address=EvmAddress.from_string("302a300506032b6570032100114e6abc371b82da"),
    )
    account_id4 = AccountId(shard=0, realm=0, num=0, evm_address=None)

    assert account_id1 == account_id2
    assert account_id1 != account_id3
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


def test_evm_address_affects_string_representation(evm_address):
    """Test that evm_address changes string representation behavior."""
    account_id1 = AccountId(shard=0, realm=0, num=0, evm_address=evm_address)
    account_id2 = AccountId(shard=0, realm=0, num=100)

    str1 = str(account_id1)
    str2 = str(account_id2)

    assert str1 != str2

    assert evm_address.to_string() in str1
    assert str2 == "0.0.100"


def test_validate_checksum_for_id(client):
    """Test validateChecksum for accountId"""
    account_id = AccountId.from_string("0.0.100-hhghj")
    account_id.validate_checksum(client)


def test_validate_checksum_with_alias_key_set(client, alias_key):
    """Test validateChecksum should raise ValueError if aliasKey is set"""
    account_id = AccountId.from_string("0.0.100-hhghj")
    account_id.alias_key = alias_key

    with pytest.raises(
        ValueError,
        match="Cannot calculate checksum with an account ID that has a aliasKey or evmAddress",
    ):
        account_id.validate_checksum(client)


def test_validate_checksum_with_evm_address_key_set(client, evm_address):
    """Test validateChecksum should raise ValueError if evm_address is set"""
    account_id = AccountId.from_string("0.0.100-hhghj")
    account_id.evm_address = evm_address

    with pytest.raises(
        ValueError,
        match="Cannot calculate checksum with an account ID that has a aliasKey or evmAddress",
    ):
        account_id.validate_checksum(client)


def test_validate_checksum_for_invalid_checksum(client):
    """Test Invalid Checksum for Id should raise ValueError"""
    account_id = AccountId.from_string("0.0.100-abcde")

    with pytest.raises(ValueError, match="Checksum mismatch for 0.0.100"):
        account_id.validate_checksum(client)


def test_populate_account_num(evm_address):
    """Test that populate_account_num correctly queries the mirror node."""
    mock_client = MagicMock()
    mock_client.network.get_mirror_rest_url.return_value = "http://mirror_node_rest_url"

    account_id = AccountId.from_evm_address(evm_address, 0, 0)

    response = {"account": "0.0.100"}

    with patch(
        "hiero_sdk_python.account.account_id.perform_query_to_mirror_node"
    ) as mock_query:
        mock_query.return_value = response
        account_id.populate_account_num(mock_client)

    assert account_id.num == 100


def test_populate_account_num_missing_account(evm_address):
    """
    Test that populate_account_num raises a ValueError when the mirror node
    query does not return an account number.
    """
    account_id = AccountId.from_evm_address(evm_address, 0, 0)
    mock_client = MagicMock()
    mock_client.network.get_mirror_rest_url.return_value = "http://mirror_node_rest_url"

    with patch(
        "hiero_sdk_python.account.account_id.perform_query_to_mirror_node"
    ) as mock_query:
        mock_query.return_value = {}
        with pytest.raises(ValueError, match="Mirror node response missing 'account'"):
            account_id.populate_account_num(mock_client)


def test_populate_account_num_invalid_account_format(evm_address):
    """Test populate_account_num raises ValueError for invalid account format."""
    account_id = AccountId.from_evm_address(evm_address, 0, 0)
    mock_client = MagicMock()
    mock_client.network.get_mirror_rest_url.return_value = "http://mirror_node_rest_url"

    # account value cannot be split into a valid int
    response = {"account": "invalid.account.format"}

    with patch(
        "hiero_sdk_python.account.account_id.perform_query_to_mirror_node"
    ) as mock_query:
        mock_query.return_value = response
        with pytest.raises(
            ValueError, match="Invalid account format received: invalid.account.format"
        ):
            account_id.populate_account_num(mock_client)


def test_populate_account_num_missing_evm_address():
    """Test that populate_account_num raises a ValueError when evm_address is none."""
    account_id = AccountId.from_string("0.0.100")
    mock_client = MagicMock()

    with pytest.raises(
        ValueError, match="Account evm_address is required before populating num"
    ):
        account_id.populate_account_num(mock_client)


def test_populate_account_num_mirror_node_failure():
    """Test populate_account_num should wrap mirror node RuntimeError with context"""
    evm_address = EvmAddress.from_string("0x" + "11" * 20)
    account_id = AccountId.from_evm_address(evm_address, 0, 0)

    mock_client = MagicMock()
    mock_client.network.get_mirror_rest_url.return_value = "http://mirror-node"

    with patch(
        "hiero_sdk_python.account.account_id.perform_query_to_mirror_node",
        side_effect=RuntimeError("mirror node query error"),
    ):
        with pytest.raises(
            RuntimeError,
            match="Failed to populate account number from mirror node for evm_address",
        ):
            account_id.populate_account_num(mock_client)


def test_populate_account_evm_address(evm_address):
    """Test that populate_evm_address correctly queries the mirror node."""
    mock_client = MagicMock()
    mock_client.network.get_mirror_rest_url.return_value = "http://mirror_node_rest_url"

    account_id = AccountId.from_string("0.0.100")

    response = {"evm_address": evm_address.to_string()}

    with patch(
        "hiero_sdk_python.account.account_id.perform_query_to_mirror_node"
    ) as mock_query:
        mock_query.return_value = response
        account_id.populate_evm_address(mock_client)

    assert account_id.evm_address == evm_address


def test_populate_evm_address_response_missing_evm_address():
    """
    Test that populate_evm_address raises a ValueError when the mirror node
    query does not return an account evm_address.
    """
    account_id = AccountId.from_string("0.0.100")
    mock_client = MagicMock()
    mock_client.network.get_mirror_rest_url.return_value = "http://mirror_node_rest_url"

    with patch(
        "hiero_sdk_python.account.account_id.perform_query_to_mirror_node"
    ) as mock_query:
        mock_query.return_value = {}
        with pytest.raises(
            ValueError, match="Mirror node response missing 'evm_address': {}"
        ):
            account_id.populate_evm_address(mock_client)


def test_populate_evm_address_missing_num(evm_address):
    """Test that populate_account_num raises a ValueError when num is none."""
    account_id = AccountId.from_evm_address(evm_address, 0, 0)  # num == 0
    mock_client = MagicMock()

    with pytest.raises(
        ValueError, match="Account number is required before populating evm_address"
    ):
        account_id.populate_evm_address(mock_client)


def test_populate_evm_address_mirror_node_failure():
    """Test populate_evm_address should wrap mirror node RuntimeError with context"""
    account_id = AccountId(shard=0, realm=0, num=123)

    mock_client = MagicMock()
    mock_client.network.get_mirror_rest_url.return_value = "http://mirror-node"

    with patch(
        "hiero_sdk_python.account.account_id.perform_query_to_mirror_node",
        side_effect=RuntimeError("mirror node query error"),
    ):
        with pytest.raises(
            RuntimeError,
            match="Failed to populate evm_address from mirror node for account 123",
        ):
            account_id.populate_evm_address(mock_client)


def test_populate_evm_address_requires_account_num():
    """Test populate_evm_address should raise ValueError when num is None"""
    account_id = AccountId(shard=0, realm=0, num=None)

    mock_client = MagicMock()

    with pytest.raises(
        ValueError, match="Account number is required before populating evm_address"
    ):
        account_id.populate_evm_address(mock_client)


def test_to_bytes_and_from_bytes_roundtrip():
    """Ensure basic numeric AccountId converts to bytes and back."""
    account_id = AccountId(0, 0, 100)
    account_id_bytes = account_id.to_bytes()

    assert account_id_bytes is not None

    # Verify
    new_account_id = AccountId.from_bytes(account_id_bytes)
    assert new_account_id is not None

    assert new_account_id.shard == account_id.shard
    assert new_account_id.realm == account_id.realm
    assert new_account_id.num == account_id.num
    assert new_account_id.alias_key == account_id.alias_key
    assert new_account_id.evm_address == account_id.evm_address


def test_get_evm_address_from_account_num():
    """Test to_evm_address return the evm_address using the account num"""
    account_id = AccountId.from_string("0.0.100")
    assert account_id.to_evm_address() is not None


def test_to_bytes_and_from_bytes_with_alias_key(alias_key):
    """Ensure alias key survives byte round-trip."""
    account_id = AccountId(0, 0, 0, alias_key=alias_key)
    account_id_bytes = account_id.to_bytes()

    assert account_id_bytes is not None

    # Verify
    new_account_id = AccountId.from_bytes(account_id_bytes)
    assert new_account_id is not None

    assert new_account_id.shard == account_id.shard
    assert new_account_id.realm == account_id.realm
    # account.num is set to 0 as alias is set
    assert new_account_id.alias_key.__eq__(account_id.alias_key)
    assert new_account_id.evm_address == account_id.evm_address


def test_to_bytes_and_from_bytes_with_evm_address(evm_address):
    """Ensure EVM address survives byte round-trip."""
    account_id = AccountId(0, 0, 0, evm_address=evm_address)
    account_id_bytes = account_id.to_bytes()

    assert account_id_bytes is not None

    # Verify
    new_account_id = AccountId.from_bytes(account_id_bytes)
    assert new_account_id is not None

    assert new_account_id.shard == account_id.shard
    assert new_account_id.realm == account_id.realm
    # account.num is set to 0 as alias is set
    assert new_account_id.alias_key == account_id.alias_key
    assert new_account_id.evm_address == account_id.evm_address


def test_to_evm_address_returns_existing_evm_address(evm_address):
    """Test to_evm_address returns stored evm_address if present."""
    account_id = AccountId(shard=0, realm=0, num=0, evm_address=evm_address)

    result = account_id.to_evm_address()

    assert result == evm_address.to_string()


def test_from_evm_address_with_hex_string():
    """Test AccountId from a valid 0x-prefixed EVM address string should succeed."""
    evm_str = "1234567890abcdef1234567890abcdef12345678"
    evm_str_with_prefix = f"0x{evm_str}"

    account_id = AccountId.from_evm_address(evm_str, shard=0, realm=0)

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key is None
    assert account_id.evm_address is not None
    assert account_id.evm_address.to_string() == evm_str.lower()

    # with prefix '0x'
    account_id = AccountId.from_evm_address(evm_str_with_prefix, shard=0, realm=0)

    assert account_id.shard == 0
    assert account_id.realm == 0
    assert account_id.num == 0
    assert account_id.alias_key is None
    assert account_id.evm_address is not None
    assert account_id.evm_address.to_string() == evm_str.lower()


def test_from_evm_address_none():
    """Passing None as evm_address should raise ValueError."""
    with pytest.raises(ValueError, match="evm_address must not be None"):
        AccountId.from_evm_address(None, shard=0, realm=0)


def test_from_evm_address_invalid_type():
    """Test passing an invalid type as evm_address should raise ValueError."""
    evm_address = 12345
    with pytest.raises(
        TypeError,
        match=f"evm_address must be a str or EvmAddress, got {type(evm_address).__name__}",
    ):
        AccountId.from_evm_address(evm_address, shard=0, realm=0)


def test_from_evm_address_invalid_string():
    """Test passing an invalid EVM address string should raise ValueError."""
    with pytest.raises(ValueError, match="Invalid EVM address string"):
        AccountId.from_evm_address("0xINVALID", shard=0, realm=0)
