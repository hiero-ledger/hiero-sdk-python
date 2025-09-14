from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
import pytest

from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.utils.entity_id_helper import (
    parse_from_string,
    generate_checksum,
    validate_checksum,
    format_to_string,
    format_to_string_with_checksum
)

pytestmark = pytest.mark.unit

def test_parse_parse_entity_id_from_string():
    """Entity ID can be parsed from string with or without checksum"""
    # Without checksum
    address = "0.0.123"
    token_id = parse_from_string(TokenId, address)

    assert token_id.shard == 0
    assert token_id.realm == 0
    assert token_id.num == 123
    assert token_id.checksum is None

    # With checksum
    address = "0.0.123-vfmkw"
    token_id = parse_from_string(TokenId, address)
    
    assert token_id.shard == 0
    assert token_id.realm == 0
    assert token_id.num == 123
    assert token_id.checksum == "vfmkw"

def test_parse_from_string_for_invalid_addresses():
    """Invalid entity ID strings should raise ValueError"""
    invalid_addresses = [
        "0.00.123",
        "0.0.123-VFMKW",
        "0.0.123#vfmkw",
        "0.0.123-vFmKw"
        "0.0.123vfmkw"
        "0.0.123 - vfmkw"
        "0.123"
        "0.0.123."
        "0.0.123-vf"
        "0.0.123-vfm-kw"
    ]

    for address in invalid_addresses:
        with pytest.raises(ValueError, match="Invalid address format"):
            parse_from_string(TokenId, address)

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

def test_validate_checksum():
    """Valid checksum should pass without error"""
    client = Client(network=Network("mainnet"))

    validate_checksum(0, 0, 1, 'dfkxr', client)

def test_validate_checksum_for_invalid():
    """Invalid checksum or missing ledger_id should raise ValueError"""
    # Mismatched checksum
    client = Client(network=Network("mainnet"))

    with pytest.raises(ValueError, match="Checksum mismatch for 0.0.4"):
        validate_checksum(0, 0, 4, "dfkxr", client)

    # Missing ledger_id
    client.network.ledger_id = None

    with pytest.raises(ValueError, match="Missing ledger ID in client"):
        validate_checksum(0, 0, 1, "dfkxr", client)

def test_format_to_string():
    """Entity ID should format correctly without checksum"""
    assert format_to_string(0, 0, 4) == '0.0.4'

def test_format_to_string_with_checksum():
    """Entity ID should format correctly with checksum"""
    client = Client(network=Network("mainnet"))
    checksum = 'dfkxr'

    assert format_to_string_with_checksum(0, 0, 1, client) == f'0.0.1-{checksum}'

def test_parse_and_format_with_checksum():
    """Parsing then formatting should preserve entity ID + checksum"""
    client = Client(network=Network("mainnet"))

    original = '0.0.1-dfkxr'
    parsed = parse_from_string(TokenId, original)
    formatted = format_to_string_with_checksum(parsed.shard, parsed.realm, parsed.num, client)

    assert formatted == original

def test_parse_and_format_without_checksum():
    """Parsing then formatting should preserve entity ID without checksum"""
    original = '0.0.123'
    parsed = parse_from_string(TokenId, original)
    formatted = format_to_string(parsed.shard, parsed.realm, parsed.num)

    assert formatted == original