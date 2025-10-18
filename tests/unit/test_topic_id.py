import pytest

from hiero_sdk_python.consensus.topic_id import TopicId

pytestmark = pytest.mark.unit

@pytest.fixture
def client(mock_client):
    mock_client.network.ledger_id = bytes.fromhex("00") # mainnet ledger id
    return mock_client

def test_default_initialization():
    """Test TopicId initialization with default values."""
    topic_id = TopicId()
    
    assert topic_id.shard == 0
    assert topic_id.realm == 0
    assert topic_id.num == 0
    assert topic_id.checksum == None

def test_custom_initialization():
    """Test TopicId initialization with custom values."""
    topic_id = TopicId(shard=1, realm=2, num=3)
    
    assert topic_id.shard == 1
    assert topic_id.realm == 2
    assert topic_id.num == 3
    assert topic_id.checksum == None

def test_str_representation():
    """Test string representation of TopicId."""
    topic_id = TopicId(shard=1, realm=2, num=3)
    
    assert str(topic_id) == "1.2.3"

def test_str_representation_default():
    """Test string representation of TopicId with default values."""
    topic_id = TopicId()
    
    assert str(topic_id) == "0.0.0"

def test_from_string_valid():
    """Test creating TopicId from valid string format."""
    topic_id = TopicId.from_string("1.2.3")
    
    assert topic_id.shard == 1
    assert topic_id.realm == 2
    assert topic_id.num == 3
    assert topic_id.checksum == None

def test_from_string_with_spaces():
    """Test creating TopicId from string with leading/trailing spaces."""
    topic_id = TopicId.from_string("1.2.3")
    
    assert topic_id.shard == 1
    assert topic_id.realm == 2
    assert topic_id.num == 3
    assert topic_id.checksum == None

def test_from_string_zeros():
    """Test creating TopicId from string with zero values."""
    topic_id = TopicId.from_string("0.0.0")
    
    assert topic_id.shard == 0
    assert topic_id.realm == 0
    assert topic_id.num == 0
    assert topic_id.checksum == None

def test_from_string_large_numbers():
    """Test creating TopicId from string with large numbers."""
    topic_id = TopicId.from_string("999.888.777")
    
    assert topic_id.shard == 999
    assert topic_id.realm == 888
    assert topic_id.num == 777
    assert topic_id.checksum == None

def test_from_string_with_checksum():
    """Test creating TopicId from string with leading/trailing spaces."""
    topic_id = TopicId.from_string("1.2.3-abcde")
    
    assert topic_id.shard == 1
    assert topic_id.realm == 2
    assert topic_id.num == 3
    assert topic_id.checksum == "abcde"

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
def test_from_string_for_invalid_format(invalid_id):
    """Should raise error when creating TopicId from invalid string input."""
    with pytest.raises((TypeError, ValueError)):
        TopicId.from_string(invalid_id)

def test_str_representaion_with_checksum(client):
    """Should return string with checksum when ledger id is provided."""
    topic_id = TopicId.from_string("0.0.1")
    assert topic_id.to_string_with_checksum(client) == "0.0.1-dfkxr"

def test_validate_checksum_success(client):
    """Should pass checksum validation when checksum is correct."""
    topic_id = TopicId.from_string("0.0.1-dfkxr")
    topic_id.validate_checksum(client)

def test_validate_checksum_failure(client):
    """Should raise ValueError if checksum validation fails."""
    topic_id = TopicId.from_string("0.0.1-wronx")

    with pytest.raises(ValueError):
        topic_id.validate_checksum(client)
