"""Tests for the key_utils module."""

import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.utils.key_utils import Key, key_to_proto

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


def test_key_to_proto_with_invalid_string_raises_error():
    """Tests key_to_proto raises TypeError with invalid input."""
    with pytest.raises(TypeError) as e:
        key_to_proto("this is not a key")

    assert "Key must be of type PrivateKey or PublicKey" in str(e.value)


def test_key_type_alias():
    """Tests that the Key type alias works correctly."""
    private_key = PrivateKey.generate_ed25519()
    public_key = private_key.public_key()

    # Test that both PrivateKey and PublicKey can be assigned to Key type
    key1: Key = private_key
    key2: Key = public_key

    # Both should work with key_to_proto
    assert key_to_proto(key1) is not None
    assert key_to_proto(key2) is not None
