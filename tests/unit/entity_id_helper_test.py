from unittest.mock import MagicMock, patch
import pytest
import struct
import requests

from hiero_sdk_python.utils.entity_id_helper import (
    parse_from_string,
    generate_checksum,
    perform_query_to_mirror_node,
    to_solidity_address,
    validate_checksum,
    format_to_string,
    format_to_string_with_checksum
)

pytestmark = pytest.mark.unit

def test_parse_parse_entity_id_from_string():
    """Entity ID can be parsed from string with or without checksum"""
    # Without checksum
    address = "0.0.123"
    shard, realm, num, checksum = parse_from_string(address)

    assert shard == '0'
    assert realm == '0'
    assert num == '123'
    assert checksum is None

    # With checksum
    address = "0.0.123-vfmkw"
    shard, realm, num, checksum= parse_from_string(address)
 
    assert shard == '0'
    assert realm == '0'
    assert num == '123'
    assert checksum == "vfmkw"

@pytest.mark.parametrize(
    'invalid_address',
    [
        "0.00.123",
        "0.0.123-VFMKW",
        "0.0.123#vfmkw",
        "0.0.123-vFmKw",
        "0.0.123vfmkw",
        "0.0.123 - vfmkw",
        "0.123",
        "0.0.123.",
        "0.0.123-vf",
        "0.0.123-vfm-kw"
    ],
)
def test_parse_from_string_for_invalid_addresses(invalid_address):
    """Invalid entity ID strings should raise ValueError"""
    with pytest.raises(ValueError, match="Invalid format for entity ID"):
        parse_from_string(invalid_address)

def test_generate_checksum():
    """Checksum generation"""
    ledger_id = bytes.fromhex("00") # mainnet ledger_id
    assert generate_checksum(ledger_id, '0.0.1') == 'dfkxr'

    ledger_id = bytes.fromhex("01") # testnet ledger_id
    assert generate_checksum(ledger_id, '0.0.1') == 'mswfa'

    ledger_id = bytes.fromhex("02") # previewnet ledger_id
    assert generate_checksum(ledger_id, '0.0.1') == 'wghmj'

    ledger_id = bytes.fromhex("03") # solo/local ledger_id
    assert generate_checksum(ledger_id, '0.0.1') == 'ftsts'

def test_validate_checksum(mock_client):
    """Valid checksum should pass without error"""
    client = mock_client
    client.network.ledger_id = bytes.fromhex("00")

    validate_checksum(0, 0, 1, 'dfkxr', client)

def test_validate_checksum_for_invalid(mock_client):
    """Invalid checksum or missing ledger_id should raise ValueError"""
    # Mismatched checksum
    client = mock_client
    client.network.ledger_id = bytes.fromhex("00")

    with pytest.raises(ValueError, match="Checksum mismatch for 0.0.4"):
        validate_checksum(0, 0, 4, "dfkxr", client)

    # Missing ledger_id
    client.network.ledger_id = None

    with pytest.raises(ValueError, match="Missing ledger ID in client"):
        validate_checksum(0, 0, 1, "dfkxr", client)

def test_format_to_string():
    """Entity ID should format correctly without checksum"""
    assert format_to_string(0, 0, 4) == '0.0.4'

def test_format_to_string_with_checksum(mock_client):
    """Entity ID should format correctly with checksum"""
    client = mock_client
    client.network.ledger_id = bytes.fromhex("00")

    checksum = 'dfkxr'

    assert format_to_string_with_checksum(0, 0, 1, client) == f'0.0.1-{checksum}'

def test_parse_and_format_with_checksum(mock_client):
    """Parsing then formatting should preserve entity ID + checksum"""
    client = mock_client
    client.network.ledger_id = bytes.fromhex("00")

    original = '0.0.1-dfkxr'
    shard, realm, num, _ = parse_from_string(original)
    formatted = format_to_string_with_checksum(shard, realm, num, client)

    assert formatted == original

def test_parse_and_format_without_checksum():
    """Parsing then formatting should preserve entity ID without checksum"""
    original = '0.0.123'
    shard, realm, num, _ = parse_from_string(original)
    formatted = format_to_string(shard, realm, num)

    assert formatted == original

def test_to_solidity_address_valid():
    shard, realm, num = 0, 0, 1001
    result = to_solidity_address(shard, realm, num)

    # Expect raw packed bytes
    expected = struct.pack(">iqq", shard, realm, num).hex()

    assert result == expected
    assert len(result) == 40  # exactly 20 bytes
    assert result.islower()

def test_to_solidity_address_zero_values():
    assert to_solidity_address(0, 0, 0) == ("00" * 20)

def test_to_solidity_address_out_of_range():
    shard, realm, num = 2**31, 0, 0
    with pytest.raises(ValueError, match="shard out of 32-bit range"):
        to_solidity_address(shard, realm, num)

def test_perform_query_to_mirror_node_success():
    """Test successful mirror node response without requests_mock."""
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"account": "0.0.777"}
    mock_response.raise_for_status.return_value = None

    with patch("hiero_sdk_python.utils.entity_id_helper.requests.get", return_value=mock_response):
        result = perform_query_to_mirror_node("http://mirror-node/accounts/123")
        assert result == {"account": "0.0.777"}

def test_perform_query_to_mirror_node_failure():
    """Test mirror node failure handling."""
    
    with patch("hiero_sdk_python.utils.entity_id_helper.requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("boom")

        with pytest.raises(RuntimeError, match="Unexpected error while querying mirror node:"):
            perform_query_to_mirror_node("http://mirror-node/accounts/123")


def test_perform_query_to_mirror_node_http_error():
    """
    Test that perform_query_to_mirror_node raises a RuntimeError when requests.get returns an HTTPError.
    """
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP fail")

    with patch("hiero_sdk_python.utils.entity_id_helper.requests.get", return_value=mock_response):
        with pytest.raises(RuntimeError, match="Mirror node request failed"):
            perform_query_to_mirror_node("http://mirror-node/accounts/123")


def test_perform_query_to_mirror_node_connection_error():
    """
    Test that perform_query_to_mirror_node raises a RuntimeError when requests.get raises a ConnectionError.
    """
    with patch(
        "hiero_sdk_python.utils.entity_id_helper.requests.get",
        side_effect=requests.exceptions.ConnectionError("Connection fail")
    ):
        with pytest.raises(RuntimeError, match="Mirror node request failed"):
            perform_query_to_mirror_node("http://mirror-node/accounts/123")


def test_perform_query_to_mirror_node_timeout():
    """
    Test that perform_query_to_mirror_node raises a RuntimeError when requests.get raises a Timeout exception.
    """
    with patch(
        "hiero_sdk_python.utils.entity_id_helper.requests.get",
        side_effect=requests.exceptions.Timeout("Timeout")
    ):
        with pytest.raises(RuntimeError, match="Mirror node request timed out"):
            perform_query_to_mirror_node("http://mirror-node/accounts/123")

def test_perform_query_to_mirror_node_invalid_url_none():
    """Test url must be a non-empty string (None case)."""
    with pytest.raises(ValueError, match="url must be a non-empty string"):
        perform_query_to_mirror_node(None)

def test_perform_query_to_mirror_node_invalid_url_empty():
    """Test url must be a non-empty string (empty string case)."""
    with pytest.raises(ValueError, match="url must be a non-empty string"):
        perform_query_to_mirror_node("")
