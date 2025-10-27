import pytest

from hiero_sdk_python.tokens.token_id import TokenId

pytestmark = pytest.mark.unit

def test_create_token_id_from_string():
    """Should correctly create TokenId from string input, with and without checksum."""
    # Without checksum
    token_id = TokenId.from_string('0.0.1')

    assert token_id.shard == 0
    assert token_id.realm == 0
    assert token_id.num == 1
    assert token_id.checksum is None

    # With checksum
    token_id = TokenId.from_string('0.0.1-dfkxr')

    assert token_id.shard == 0
    assert token_id.realm == 0
    assert token_id.num == 1
    assert token_id.checksum == 'dfkxr'

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
    """Should raise error when creating TokenId from invalid string input."""
    with pytest.raises((TypeError, ValueError)):
        TokenId.from_string(invalid_id)

def test_str_representaion_with_checksum(mock_client):
    """Should return string with checksum when ledger id is provided."""
    client = mock_client
    client.network.ledger_id = bytes.fromhex("00")

    token_id = TokenId.from_string("0.0.1")
    assert token_id.to_string_with_checksum(client) == "0.0.1-dfkxr"

def test_validate_checksum_success(mock_client):
    """Should pass checksum validation when checksum is correct."""
    client = mock_client
    client.network.ledger_id = bytes.fromhex("00")
    token_id = TokenId.from_string("0.0.1-dfkxr")

    token_id.validate_checksum(client)

def test_validate_checksum_failure(mock_client):
    """Should raise ValueError if checksum validation fails."""
    client = mock_client
    client.network.ledger_id = bytes.fromhex("00")
    token_id = TokenId.from_string("0.0.1-wronx")

    with pytest.raises(ValueError):
        token_id.validate_checksum(client)
