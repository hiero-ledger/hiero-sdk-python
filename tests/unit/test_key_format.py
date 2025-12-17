"""Tests for the key_format module."""

import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.utils.key_utils import key_to_proto
from hiero_sdk_python.utils.key_format import format_key

pytestmark = pytest.mark.unit

def test_format_key_ed25519():
    """Test formatting an Ed25519 key."""
    private_key = PrivateKey.generate_ed25519()
    public_key = private_key.public_key()

    proto_key = key_to_proto(public_key)
    formatted = format_key(proto_key)

    expected = f"ed25519({public_key.to_bytes_raw().hex()})"

    assert formatted == expected

def test_format_key_none():
    """Test formatting a None key."""
    formatted = format_key(None)

    assert formatted == "None" 

def test_format_key_threshold_key():
    """Test formatting a ThresholdKey."""

    key = basic_types_pb2.Key()
    key.thresholdKey.threshold = 2

    formatted = format_key(key)

    assert formatted == "thresholdKey(...)"

def test_format_key_contract_id():
    """Test formatting a ContractID key."""

    key = basic_types_pb2.Key()
    key.contractID.shardNum = 0
    key.contractID.realmNum = 0
    key.contractID.contractNum = 5678

    expected_inner = str(key.contractID) 
    expected = f"contractID({expected_inner})"

    formatted = format_key(key)

    assert formatted == expected

def test_format_key_keylist():
    """Test formatting a KeyList."""

    key = basic_types_pb2.Key()
    key.keyList.keys.add()

    formatted = format_key(key)

    assert formatted == "keyList(...)"

def test_format_key_unknown():
    """Test formatting an unknown key type."""
    key = basic_types_pb2.Key()
    # Intentionally not setting any known key type

    formatted = format_key(key)
    expected = str(key).replace("\n", " ")

    assert formatted == expected