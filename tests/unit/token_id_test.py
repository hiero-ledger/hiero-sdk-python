from __future__ import annotations

import pytest

from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId


pytestmark = pytest.mark.unit


def test_create_token_id_from_string():
    """Should correctly create TokenId from string input, with and without checksum."""
    # Without checksum
    token_id = TokenId.from_string("0.0.1")

    assert token_id.shard == 0
    assert token_id.realm == 0
    assert token_id.num == 1
    assert token_id.checksum is None

    # With checksum
    token_id = TokenId.from_string("0.0.1-dfkxr")

    assert token_id.shard == 0
    assert token_id.realm == 0
    assert token_id.num == 1
    assert token_id.checksum == "dfkxr"


@pytest.mark.parametrize(
    "invalid_id",
    [
        "1.2",  # Too few parts
        "1.2.3.4",  # Too many parts
        "a.b.c",  # Non-numeric parts
        "",  # Empty string
        "1.a.3",  # Partial numeric
        123,
        None,
        "0.0.-1",
        "abc.def.ghi",
        "0.0.1-ad",
        "0.0.1-addefgh",
        "0.0.1 - abcde",
        " 0.0.100 ",
    ],
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


def test_token_id_repr():
    """Should return constructor-style representation without checksum."""
    token_id = TokenId(0, 0, 123)
    assert repr(token_id) == "TokenId(shard=0, realm=0, num=123)"

    # Test with different values
    token_id2 = TokenId(1, 2, 456)
    assert repr(token_id2) == "TokenId(shard=1, realm=2, num=456)"


def test_token_id_nft_returns_correct_identifier():
    """Should create an NFT identifier for this token and serial."""
    token_id = TokenId(0, 0, 1234)

    nft = token_id.nft(5)

    assert isinstance(nft, NftId)
    assert nft.token_id == token_id
    assert nft.serial_number == 5


@pytest.mark.parametrize("serial", [0, -1, -10])
def test_token_id_nft_rejects_non_positive_serial(serial):
    """Should reject serial numbers that are not positive."""
    token_id = TokenId(0, 0, 1234)

    with pytest.raises(ValueError):
        token_id.nft(serial)


@pytest.mark.parametrize("serial", ["1", 1.5, None, True])
def test_token_id_nft_rejects_invalid_serial_type(serial):
    """Should reject serial values that are not integers."""
    token_id = TokenId(0, 0, 1234)

    with pytest.raises(TypeError):
        token_id.nft(serial)


def test_token_id_nft_rejects_serial_above_int64_max():
    """Should reject serial numbers outside the protobuf int64 range."""
    token_id = TokenId(0, 0, 1234)

    with pytest.raises(ValueError):
        token_id.nft(1 << 63)


def test_token_id_nft_accepts_int64_max():
    """Should accept the maximum valid protobuf int64 serial."""
    token_id = TokenId(0, 0, 1234)
    max_serial = (1 << 63) - 1

    nft = token_id.nft(max_serial)

    assert isinstance(nft, NftId)
    assert nft.token_id == token_id
    assert nft.serial_number == max_serial
    assert nft._to_proto().serial_number == max_serial
