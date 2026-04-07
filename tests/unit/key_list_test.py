from __future__ import annotations

import pytest

from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services import basic_types_pb2


pytestmark = pytest.mark.unit


def make_keys(n=3):
    """Helper to generate a list of public keys."""
    keys = []
    for _ in range(n):
        priv = PrivateKey.generate("ed25519")
        keys.append(priv.public_key())
    return keys


def test_create_keylist_no_threshold():
    """Test create a KeyList without a threshold."""
    keys = make_keys(3)
    kl = KeyList(keys)

    assert kl.threshold is None
    assert len(kl.keys) == 3


def test_create_keylist_with_threshold():
    """Test create a KeyList with a threshold."""
    keys = make_keys(3)
    kl = KeyList(keys, threshold=2)

    assert kl.threshold == 2
    assert len(kl.keys) == 3


def test_create_keylist_empty():
    """Test KeyList can be created without providing keys."""
    kl = KeyList()

    assert kl.threshold is None
    assert kl.keys == []


def test_constructor_type_check_keys():
    """Test constructor should reject non-list keys."""
    with pytest.raises(TypeError, match="keys must be a list"):
        KeyList("not-a-list")


def test_constructor_type_check_key_elements():
    """Test constructor should reject non-Key objects in list."""
    with pytest.raises(TypeError, match="instances of Key"):
        KeyList([1, 2, 3])


def test_constructor_threshold_type_check():
    """Test constructor should reject non-int threshold."""
    with pytest.raises(TypeError, match="threshold must be an integer"):
        KeyList(make_keys(2), threshold="two")


def test_add_key():
    """Test add_key appends a key and returns self."""
    kl = KeyList()

    key = PrivateKey.generate("ed25519").public_key()
    returned = kl.add_key(key)

    assert returned is kl
    assert kl.keys == [key]


def test_add_key_type_check():
    """Test add_key should reject non-Key objects."""
    kl = KeyList()

    with pytest.raises(TypeError, match="instances of Key"):
        kl.add_key("not-a-key")


def test_set_keys():
    """Test set_keys replaces existing keys."""
    kl = KeyList(make_keys(2))

    new_keys = make_keys(3)
    returned = kl.set_keys(new_keys)

    assert returned is kl
    assert kl.keys == new_keys


def test_set_keys_type_check():
    """Test set_keys should reject non-list input."""
    kl = KeyList()

    with pytest.raises(TypeError, match="keys must be a list"):
        kl.set_keys("not-a-list")


def test_set_keys_invalid_elements():
    """Test set_keys should reject non-Key elements."""
    kl = KeyList()

    with pytest.raises(TypeError, match="instances of Key"):
        kl.set_keys([1, 2])


def test_set_threshold():
    """Test threshold can be updated."""
    kl = KeyList(make_keys(3))

    returned = kl.set_threshold(2)

    assert returned is kl
    assert kl.threshold == 2


def test_set_threshold_none():
    """Test threshold can be reset to None."""
    kl = KeyList(make_keys(3), threshold=2)

    kl.set_threshold(None)

    assert kl.threshold is None


def test_set_threshold_type_check():
    """Test set_threshold should reject non-int values."""
    kl = KeyList(make_keys(2))

    with pytest.raises(TypeError, match="threshold must be an integer"):
        kl.set_threshold("bad")


def test_to_proto_without_threshold():
    """Test to_proto should produce a protobuf KeyList."""
    keys = make_keys(3)
    kl = KeyList(keys)

    proto = kl.to_proto()

    assert isinstance(proto, basic_types_pb2.KeyList)
    assert len(proto.keys) == 3


def test_to_proto_with_threshold():
    """Test to_proto_key should produce a ThresholdKey if threshold is set."""
    keys = make_keys(3)
    kl = KeyList(keys, threshold=2)

    proto_key = kl.to_proto_key()

    assert proto_key.HasField("thresholdKey")
    assert proto_key.thresholdKey.threshold == 2
    assert len(proto_key.thresholdKey.keys.keys) == 3


def test_to_proto_key_without_threshold():
    """Test to_proto_key should produce a standard KeyList if no threshold."""
    kl = KeyList(make_keys(2))

    proto_key = kl.to_proto_key()

    assert proto_key.HasField("keyList")
    assert len(proto_key.keyList.keys) == 2


def test_from_proto_keylist():
    """Test from_proto correctly reconstructs a KeyList."""
    keys = make_keys(3)
    kl = KeyList(keys)

    proto = kl.to_proto()

    loaded = KeyList.from_proto(proto)

    assert isinstance(loaded, KeyList)
    assert len(loaded.keys) == 3
    assert loaded.threshold is None


def test_from_proto_threshold():
    """Test thresholdKey proto loads correctly."""
    keys = make_keys(3)
    kl = KeyList(keys, threshold=2)

    proto_key = kl.to_proto_key()

    loaded = KeyList.from_proto(proto_key.thresholdKey.keys, threshold=proto_key.thresholdKey.threshold)

    assert loaded.threshold == 2
    assert len(loaded.keys) == 3


@pytest.mark.parametrize("num_keys", [1, 2, 5])
def test_proto_roundtrip(num_keys):
    """Test roundtrip should preserve key count."""
    kl1 = KeyList(make_keys(num_keys), threshold=None)

    proto = kl1.to_proto()
    kl2 = KeyList.from_proto(proto)

    assert len(kl1.keys) == len(kl2.keys)


def test_keylist_is_instance_of_key():
    """Test KeyList must inherit from Key."""
    kl = KeyList()
    assert isinstance(kl, Key)
