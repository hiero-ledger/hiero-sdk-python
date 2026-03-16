"""Tests for the key_utils module."""

import pytest

from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.threshold_key import ThresholdKey
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.utils.key_utils import (
    Key,
    contains_empty_key_list,
    key_from_proto,
    key_to_proto,
)

pytestmark = pytest.mark.unit


def test_key_to_proto_with_ed25519_public_key():
    """Tests key_to_proto with an Ed25519 PublicKey."""
    private_key = PrivateKey.generate_ed25519()
    public_key = private_key.public_key()

    expected_proto = public_key._to_proto()
    result_proto = key_to_proto(public_key)

    assert result_proto == expected_proto
    assert isinstance(result_proto, basic_types_pb2.Key)


def test_key_to_proto_with_ecdsa_public_key():
    """Tests key_to_proto with an ECDSA PublicKey."""
    private_key = PrivateKey.generate_ecdsa()
    public_key = private_key.public_key()

    expected_proto = public_key._to_proto()
    result_proto = key_to_proto(public_key)

    assert result_proto == expected_proto
    assert isinstance(result_proto, basic_types_pb2.Key)


def test_key_to_proto_with_ed25519_private_key():
    """Tests key_to_proto with an Ed25519 PrivateKey (extracts public key)."""
    private_key = PrivateKey.generate_ed25519()
    public_key = private_key.public_key()

    # We expect the *public key's* proto, even though we passed a private key
    expected_proto = public_key._to_proto()

    # Call the function with the PrivateKey
    result_proto = key_to_proto(private_key)

    # Assert it correctly converted it to the public key proto
    assert result_proto == expected_proto
    assert isinstance(result_proto, basic_types_pb2.Key)


def test_key_to_proto_with_ecdsa_private_key():
    """Tests key_to_proto with an ECDSA PrivateKey (extracts public key)."""
    private_key = PrivateKey.generate_ecdsa()
    public_key = private_key.public_key()

    expected_proto = public_key._to_proto()
    result_proto = key_to_proto(private_key)

    assert result_proto == expected_proto
    assert isinstance(result_proto, basic_types_pb2.Key)


def test_key_to_proto_with_none():
    """Tests key_to_proto with None."""
    result = key_to_proto(None)
    assert result is None


def test_key_to_proto_with_key_list():
    """Tests key_to_proto with a composite key list."""
    first_key = PrivateKey.generate_ed25519().public_key()
    second_key = PrivateKey.generate_ecdsa().public_key()
    key_list = KeyList([first_key, second_key])

    result_proto = key_to_proto(key_list)

    assert result_proto.HasField("keyList")
    assert list(result_proto.keyList.keys) == [first_key._to_proto(), second_key._to_proto()]


def test_key_to_proto_with_threshold_key():
    """Tests key_to_proto with a threshold key."""
    first_key = PrivateKey.generate_ed25519().public_key()
    second_key = PrivateKey.generate_ecdsa().public_key()
    threshold_key = ThresholdKey(threshold=1, keys=[first_key, second_key])

    result_proto = key_to_proto(threshold_key)

    assert result_proto.HasField("thresholdKey")
    assert result_proto.thresholdKey.threshold == 1
    assert list(result_proto.thresholdKey.keys.keys) == [first_key._to_proto(), second_key._to_proto()]


def test_key_to_proto_with_invalid_string_raises_error():
    """Tests key_to_proto raises TypeError with invalid input."""
    with pytest.raises(TypeError) as e:
        key_to_proto("this is not a key")

    assert "Key must be of type PrivateKey, PublicKey, KeyList, or ThresholdKey" in str(e.value)


def test_key_type_alias():
    """Tests that the Key type alias works correctly."""
    private_key = PrivateKey.generate_ed25519()
    public_key = private_key.public_key()
    key_list = KeyList([public_key])
    threshold_key = ThresholdKey(threshold=1, keys=[public_key])

    # Test that supported key types can be assigned to Key type
    key1: Key = private_key
    key2: Key = public_key
    key3: Key = key_list
    key4: Key = threshold_key

    # All should work with key_to_proto
    assert key_to_proto(key1) is not None
    assert key_to_proto(key2) is not None
    assert key_to_proto(key3) is not None
    assert key_to_proto(key4) is not None


def test_key_from_proto_with_key_list():
    """Tests key_from_proto with a protobuf key list."""
    first_key = PrivateKey.generate_ed25519().public_key()
    second_key = PrivateKey.generate_ecdsa().public_key()
    proto = basic_types_pb2.Key(
        keyList=basic_types_pb2.KeyList(keys=[first_key._to_proto(), second_key._to_proto()])
    )

    result = key_from_proto(proto)

    assert result == KeyList([first_key, second_key])


def test_key_from_proto_with_threshold_key():
    """Tests key_from_proto with a protobuf threshold key."""
    first_key = PrivateKey.generate_ed25519().public_key()
    second_key = PrivateKey.generate_ecdsa().public_key()
    proto = basic_types_pb2.Key(
        thresholdKey=basic_types_pb2.ThresholdKey(
            threshold=1,
            keys=basic_types_pb2.KeyList(keys=[first_key._to_proto(), second_key._to_proto()]),
        )
    )

    result = key_from_proto(proto)

    assert result == ThresholdKey(threshold=1, keys=[first_key, second_key])


def test_contains_empty_key_list_detects_top_level_empty_key_list():
    """Empty top-level key lists should be detected."""
    assert contains_empty_key_list(KeyList())


def test_contains_empty_key_list_detects_nested_empty_key_list():
    """Nested empty key lists should be detected inside threshold keys."""
    assert contains_empty_key_list(ThresholdKey(threshold=1, keys=KeyList()))


def test_contains_empty_key_list_ignores_populated_composite_keys():
    """Non-empty composite keys should pass the empty-key-list check."""
    public_key = PrivateKey.generate_ed25519().public_key()

    assert not contains_empty_key_list(KeyList([public_key]))
    assert not contains_empty_key_list(ThresholdKey(threshold=1, keys=[public_key]))
