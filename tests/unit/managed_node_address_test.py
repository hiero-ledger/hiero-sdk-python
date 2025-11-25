import pytest
from src.hiero_sdk_python.managed_node_address import _ManagedNodeAddress

pytestmark = pytest.mark.unit

def test_init():
    """Test initialization of _ManagedNodeAddress."""
    address = _ManagedNodeAddress(address="127.0.0.1", port=50211)
    assert address._address == "127.0.0.1"
    assert address._port == 50211

def test_from_string_valid():
    """Test creating _ManagedNodeAddress from a valid string."""
    address = _ManagedNodeAddress._from_string("127.0.0.1:50211")
    assert address._address == "127.0.0.1"
    assert address._port == 50211

def test_from_string_ip_address():
    """Test creating _ManagedNodeAddress from an IP address string."""
    address = _ManagedNodeAddress._from_string("35.237.200.180:50211")
    assert address._address == "35.237.200.180"
    assert address._port == 50211
    assert str(address) == "35.237.200.180:50211"

def test_from_string_url_address():
    """Test creating _ManagedNodeAddress from a URL string."""
    address = _ManagedNodeAddress._from_string("0.testnet.hedera.com:50211")
    assert address._address == "0.testnet.hedera.com"
    assert address._port == 50211
    assert str(address) == "0.testnet.hedera.com:50211"

def test_from_string_mirror_node_address():
    """Test creating _ManagedNodeAddress from a mirror node address string."""
    mirror_address = _ManagedNodeAddress._from_string("hcs.mainnet.mirrornode.hedera.com:50211")
    assert mirror_address._address == "hcs.mainnet.mirrornode.hedera.com"
    assert mirror_address._port == 50211
    assert str(mirror_address) == "hcs.mainnet.mirrornode.hedera.com:50211"

def test_from_string_invalid_format():
    """Test creating _ManagedNodeAddress from an invalid string format."""
    with pytest.raises(ValueError):
        _ManagedNodeAddress._from_string("invalid_format")

def test_from_string_invalid_string_with_spaces():
    """Test creating _ManagedNodeAddress from an invalid string with spaces."""
    with pytest.raises(ValueError):
        _ManagedNodeAddress._from_string("this is a random string with spaces:443")

def test_from_string_invalid_port():
    """Test creating _ManagedNodeAddress with invalid port."""
    with pytest.raises(ValueError):
        _ManagedNodeAddress._from_string("127.0.0.1:invalid")

def test_from_string_invalid_url_port():
    """Test creating _ManagedNodeAddress with invalid URL port."""
    with pytest.raises(ValueError):
        _ManagedNodeAddress._from_string("hcs.mainnet.mirrornode.hedera.com:notarealport")

def test_is_transport_security():
    """Test _is_transport_security method."""
    secure_address1 = _ManagedNodeAddress(address="127.0.0.1", port=50212)
    secure_address2 = _ManagedNodeAddress(address="127.0.0.1", port=443)
    insecure_address = _ManagedNodeAddress(address="127.0.0.1", port=50211)
    
    assert secure_address1._is_transport_security() is True
    assert secure_address2._is_transport_security() is True
    assert insecure_address._is_transport_security() is False

def test_string_representation():
    """Test string representation."""
    address = _ManagedNodeAddress(address="127.0.0.1", port=50211)
    assert str(address) == "127.0.0.1:50211"
    
    # Test with None address
    empty_address = _ManagedNodeAddress()
    assert str(empty_address) == "" 