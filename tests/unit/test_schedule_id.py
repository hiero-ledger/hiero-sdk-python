import pytest

from hiero_sdk_python.hapi.services.basic_types_pb2 import ScheduleID
from hiero_sdk_python.schedule.schedule_id import ScheduleId

pytestmark = pytest.mark.unit


@pytest.fixture
def client(mock_client):
    mock_client.network.ledger_id = bytes.fromhex("00") # mainnet ledger id
    return mock_client


def test_default_initialization():
    """Test ScheduleId initialization with default values."""
    schedule_id = ScheduleId()

    assert schedule_id.shard == 0
    assert schedule_id.realm == 0
    assert schedule_id.schedule == 0
    assert schedule_id.checksum is None


def test_custom_initialization():
    """Test ScheduleId initialization with custom values."""
    schedule_id = ScheduleId(shard=1, realm=2, schedule=3)

    assert schedule_id.shard == 1
    assert schedule_id.realm == 2
    assert schedule_id.schedule == 3
    assert schedule_id.checksum is None


def test_str_representation():
    """Test string representation of ScheduleId."""
    schedule_id = ScheduleId(shard=1, realm=2, schedule=3)

    assert str(schedule_id) == "1.2.3"


def test_str_representation_default():
    """Test string representation of ScheduleId with default values."""
    schedule_id = ScheduleId()

    assert str(schedule_id) == "0.0.0"


def test_from_string_valid():
    """Test creating ScheduleId from valid string format."""
    schedule_id = ScheduleId.from_string("1.2.3")

    assert schedule_id.shard == 1
    assert schedule_id.realm == 2
    assert schedule_id.schedule == 3
    assert schedule_id.checksum is None


def test_from_string_valid_with_checksum():
    """Test creating ScheduleId from valid string format."""
    schedule_id = ScheduleId.from_string("1.2.3-abcde")

    assert schedule_id.shard == 1
    assert schedule_id.realm == 2
    assert schedule_id.schedule == 3
    assert schedule_id.checksum == "abcde"

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
        ' 0.0.100 '
    ]
)
def test_from_string_invalid_formats(invalid_id):
    """Test creating ScheduleId from various invalid string formats."""
    with pytest.raises(
        ValueError, 
        match=f"Invalid schedule ID string '{invalid_id}'. Expected format 'shard.realm.schedule'"
    ):
        ScheduleId.from_string(invalid_id)


def test_to_proto():
    """Test converting ScheduleId to protobuf format."""
    schedule_id = ScheduleId(shard=1, realm=2, schedule=3)
    proto = schedule_id._to_proto()

    assert isinstance(proto, ScheduleID)
    assert proto.shardNum == 1
    assert proto.realmNum == 2
    assert proto.scheduleNum == 3


def test_from_proto():
    """Test creating ScheduleId from protobuf format."""
    proto = ScheduleID(shardNum=1, realmNum=2, scheduleNum=3)

    schedule_id = ScheduleId._from_proto(proto)

    assert schedule_id.shard == 1
    assert schedule_id.realm == 2
    assert schedule_id.schedule == 3


def test_roundtrip_proto_conversion():
    """Test that converting to proto and back preserves values."""
    original = ScheduleId(shard=5, realm=10, schedule=15)
    proto = original._to_proto()
    reconstructed = ScheduleId._from_proto(proto)

    assert original.shard == reconstructed.shard
    assert original.realm == reconstructed.realm
    assert original.schedule == reconstructed.schedule


def test_roundtrip_string_conversion():
    """Test that converting to string and back preserves values."""
    original = ScheduleId(shard=7, realm=14, schedule=21)
    string_repr = str(original)
    reconstructed = ScheduleId.from_string(string_repr)

    assert original.shard == reconstructed.shard
    assert original.realm == reconstructed.realm
    assert original.schedule == reconstructed.schedule


def test_equality():
    """Test ScheduleId equality comparison."""
    schedule_id1 = ScheduleId(shard=1, realm=2, schedule=3)
    schedule_id2 = ScheduleId(shard=1, realm=2, schedule=3)
    schedule_id3 = ScheduleId(shard=1, realm=2, schedule=4)

    assert schedule_id1 == schedule_id2
    assert schedule_id1 != schedule_id3


def test_equality_different_type():
    """Test ScheduleId equality comparison with different type."""
    schedule_id = ScheduleId(shard=1, realm=2, schedule=3)

    # Should not raise an exception and should return False
    assert schedule_id != "1.2.3"


def test_str_representation_with_checksum(client):
    """Should return string with checksum when ledger id is provided."""
    schedule_id = ScheduleId.from_string("0.0.1")
    assert schedule_id.to_string_with_checksum(client) == "0.0.1-dfkxr"


def test_validate_checksum_success(client):
    """Should pass checksum validation when checksum is correct."""
    schedule_id = ScheduleId.from_string("0.0.1-dfkxr")
    schedule_id.validate_checksum(client)


def test_validate_checksum_failure(client):
    """Should raise ValueError if checksum validation fails."""
    schedule_id = ScheduleId.from_string("0.0.1-wronx")

    with pytest.raises(ValueError, match="Checksum mismatch for 0.0.1"):
        schedule_id.validate_checksum(client)
