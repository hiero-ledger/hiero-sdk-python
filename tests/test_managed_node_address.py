import pytest
from src.hiero_sdk_python.managed_node_address import _ManagedNodeAddress


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
    
    address_secure = address._to_secure()
    assert address_secure._address == "35.237.200.180"
    assert address_secure._port == 50212
    assert str(address_secure) == "35.237.200.180:50212"
    
    address_insecure = address_secure._to_insecure()
    assert address_insecure._address == "35.237.200.180"
    assert address_insecure._port == 50211
    assert str(address_insecure) == "35.237.200.180:50211"


def test_from_string_url_address():
    """Test creating _ManagedNodeAddress from a URL string."""
    address = _ManagedNodeAddress._from_string("0.testnet.hedera.com:50211")
    assert address._address == "0.testnet.hedera.com"
    assert address._port == 50211
    assert str(address) == "0.testnet.hedera.com:50211"
    
    address_secure = address._to_secure()
    assert address_secure._address == "0.testnet.hedera.com"
    assert address_secure._port == 50212
    assert str(address_secure) == "0.testnet.hedera.com:50212"
    
    address_insecure = address_secure._to_insecure()
    assert address_insecure._address == "0.testnet.hedera.com"
    assert address_insecure._port == 50211
    assert str(address_insecure) == "0.testnet.hedera.com:50211"


def test_from_string_mirror_node_address():
    """Test creating _ManagedNodeAddress from a mirror node address string."""
    mirror_address = _ManagedNodeAddress._from_string("hcs.mainnet.mirrornode.hedera.com:50211")
    assert mirror_address._address == "hcs.mainnet.mirrornode.hedera.com"
    assert mirror_address._port == 50211
    assert str(mirror_address) == "hcs.mainnet.mirrornode.hedera.com:50211"
    
    mirror_address_secure = mirror_address._to_secure()
    assert mirror_address_secure._address == "hcs.mainnet.mirrornode.hedera.com"
    assert mirror_address_secure._port == 50212
    assert str(mirror_address_secure) == "hcs.mainnet.mirrornode.hedera.com:50212"
    
    mirror_address_insecure = mirror_address_secure._to_insecure()
    assert mirror_address_insecure._address == "hcs.mainnet.mirrornode.hedera.com"
    assert mirror_address_insecure._port == 50211
    assert str(mirror_address_insecure) == "hcs.mainnet.mirrornode.hedera.com:50211"


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


def test_to_insecure():
    """Test _to_insecure method."""
    secure_address = _ManagedNodeAddress(address="127.0.0.1", port=50212)
    insecure_address = secure_address._to_insecure()
    
    assert insecure_address._port == 50211
    assert insecure_address == secure_address  # Should be the same object
    
    # Test on already insecure address
    original_address = _ManagedNodeAddress(address="127.0.0.1", port=80)
    converted_address = original_address._to_insecure()
    assert converted_address._port == 80  # Should remain unchanged


def test_to_secure():
    """Test _to_secure method."""
    insecure_address = _ManagedNodeAddress(address="127.0.0.1", port=50211)
    secure_address = insecure_address._to_secure()
    
    assert secure_address._port == 50212
    assert secure_address == insecure_address  # Should be the same object
    
    # Test on already secure address
    original_address = _ManagedNodeAddress(address="127.0.0.1", port=443)
    converted_address = original_address._to_secure()
    assert converted_address._port == 443  # Should remain unchanged


def test_equals():
    """Test _equals method."""
    address1 = _ManagedNodeAddress(address="127.0.0.1", port=50211)
    address2 = _ManagedNodeAddress(address="127.0.0.1", port=50211)
    address3 = _ManagedNodeAddress(address="127.0.0.2", port=50211)
    address4 = _ManagedNodeAddress(address="127.0.0.1", port=50212)
    
    assert address1._equals(address2) is True
    assert address1._equals(address3) is False
    assert address1._equals(address4) is False

def test_string_representation():
    """Test string representation."""
    address = _ManagedNodeAddress(address="127.0.0.1", port=50211)
    assert str(address) == "127.0.0.1:50211"
    
    # Test with None address
    empty_address = _ManagedNodeAddress()
    assert str(empty_address) == "" 