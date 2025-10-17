import pytest

from hiero_sdk_python.consensus.topic_id import TopicId

pytestmark = pytest.mark.unit

@pytest.fixture
def client(mock_client):
    mock_client.network.ledger_id = bytes.fromhex("00") # mainnet ledger id
    return mock_client

def test_create_topic_id_from_string():
    """Should correctly create TopicId from string input, with and without checksum."""
    # Without checksum
    topic_id = TopicId.from_string('0.0.1')

    assert topic_id.shard == 0
    assert topic_id.realm == 0
    assert topic_id.num == 1
    assert topic_id.checksum is None

    # With checksum
    topic_id = TopicId.from_string('0.0.1-dfkxr')

    assert topic_id.shard == 0
    assert topic_id.realm == 0
    assert topic_id.num == 1
    assert topic_id.checksum == 'dfkxr'

@pytest.mark.parametrize(
    'invalid_id', 
    [
        '',
        123,
        None,
        '0.0.-1',
        'abc.def.ghi',
        '0.0.1-ad'
    ]
)
def test_create_topic_id_from_string_invalid_cases(invalid_id):
    """Should raise error when creating TopicId from invalid string input."""
    with pytest.raises((TypeError, ValueError)):
        TopicId.from_string(invalid_id)

def test_get_topic_id_with_checksum(client):
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
