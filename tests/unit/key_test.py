from __future__ import annotations

import pytest

from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.delegate_contract_id import DelegateContractId
from hiero_sdk_python.crypto.evm_address import EvmAddress
from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services import basic_types_pb2


pytestmark = pytest.mark.unit


class DummyKey(Key):
    """Helper Key implementation for testing."""

    def to_proto_key(self) -> basic_types_pb2.Key:
        return basic_types_pb2.Key()


def test_from_bytes_type_check():
    """Test from_bytes should reject non-bytes."""
    with pytest.raises(TypeError, match="data must be bytes"):
        Key.from_bytes("not-bytes")


def test_to_bytes_serialization():
    """Test to_bytes should serialize the proto returned by to_proto_key."""
    key = DummyKey()
    b = key.to_bytes()

    assert isinstance(b, bytes)


def test_from_proto_key_ed25519():
    """Test ed25519 keys are parsed into PublicKey objects."""
    priv = PrivateKey.generate("ed25519")
    pub = priv.public_key()

    proto = pub.to_proto_key()

    loaded = Key.from_proto_key(proto)

    assert isinstance(loaded, PublicKey)


def test_from_proto_key_ecdsa():
    """Test ECDSA keys are parsed into PublicKey objects."""
    priv = PrivateKey.generate("ecdsa")
    pub = priv.public_key()

    proto = pub.to_proto_key()

    loaded = Key.from_proto_key(proto)

    assert isinstance(loaded, PublicKey)


def test_from_proto_key_evm_address():
    """Test ECDSA_secp256k1 field is 20 bytes it should produce an EvmAddress."""
    evm = EvmAddress.from_bytes(b"\x11" * 20)

    proto = basic_types_pb2.Key(ECDSA_secp256k1=evm.address_bytes)
    loaded = Key.from_proto_key(proto)

    assert isinstance(loaded, EvmAddress)


def test_from_proto_key_contract_id():
    """Test contractID should produce a ContractId instance."""
    cid = ContractId(0, 0, 123)

    proto = basic_types_pb2.Key(contractID=cid._to_proto())

    loaded = Key.from_proto_key(proto)

    assert isinstance(loaded, ContractId)


def test_from_proto_key_delegatable_contract_id():
    """Test delegatable_contract_id should produce a ContractId instance."""
    cid = ContractId(0, 0, 123)

    proto = basic_types_pb2.Key(delegatable_contract_id=cid._to_proto())

    loaded = Key.from_proto_key(proto)

    assert isinstance(loaded, DelegateContractId)


def test_from_proto_key_keylist():
    """Test keyList should produce a KeyList instance."""
    priv = PrivateKey.generate("ed25519")

    kl = KeyList([priv.public_key()])
    proto = kl.to_proto_key()

    loaded = Key.from_proto_key(proto)

    assert isinstance(loaded, KeyList)
    assert len(loaded.keys) == 1


def test_from_proto_key_threshold_key():
    """Test thresholdKey should produce a KeyList with threshold."""
    priv = PrivateKey.generate("ed25519")

    kl = KeyList([priv.public_key()], threshold=1)
    proto = kl.to_proto_key()

    loaded = Key.from_proto_key(proto)

    assert isinstance(loaded, KeyList)
    assert loaded.threshold == 1


def test_from_proto_key_unknown_type():
    """Test unknown key type should be raised error."""
    proto = basic_types_pb2.Key()

    with pytest.raises(ValueError, match="Unknown key type"):
        Key.from_proto_key(proto)


def test_from_proto_key_type_check():
    """Test from_proto_key should reject invalid proto type."""
    with pytest.raises(TypeError, match="proto must be an instance"):
        Key.from_proto_key("not-a-proto")


def test_from_bytes_roundtrip():
    """Test a key to bytes then load with Key using from_bytes."""
    priv = PrivateKey.generate("ed25519")
    pub = priv.public_key()

    b = pub.to_bytes()

    loaded = Key.from_bytes(b)

    assert isinstance(loaded, PublicKey)


@pytest.mark.parametrize("key_type", ["ed25519", "ecdsa"])
def test_from_bytes_multiple_key_types(key_type):
    """Test from_bytes supports multiple key algorithms."""
    priv = PrivateKey.generate(key_type)
    pub = priv.public_key()

    loaded = Key.from_bytes(pub.to_bytes())

    assert isinstance(loaded, PublicKey)


def test_keylist_bytes_roundtrip():
    """Test should serialize and deserialize Key using from_bytes."""
    keys = [PrivateKey.generate("ed25519").public_key() for _ in range(2)]

    kl = KeyList(keys)

    b = kl.to_bytes()

    loaded = Key.from_bytes(b)

    assert isinstance(loaded, KeyList)
    assert len(loaded.keys) == 2


def test_threshold_key_bytes_roundtrip():
    """Test ThresholdKey should serialize and deserialize correctly."""
    keys = [PrivateKey.generate("ed25519").public_key() for _ in range(3)]

    kl = KeyList(keys, threshold=2)

    b = kl.to_bytes()

    loaded = Key.from_bytes(b)

    assert isinstance(loaded, KeyList)
    assert loaded.threshold == 2


def test_key_is_abstract():
    """Test key should not be directly instantiable."""
    with pytest.raises(TypeError):
        Key()
