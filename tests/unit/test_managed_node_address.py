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

def test_to_secure_node_port():
    """Test converting node address from plaintext to TLS port."""
    insecure = _ManagedNodeAddress(address="127.0.0.1", port=50211)
    secure = insecure._to_secure()
    
    assert secure._port == 50212
    assert secure._address == "127.0.0.1"
    assert secure._is_transport_security() is True

def test_to_secure_mirror_port():
    """Test converting mirror address from plaintext to TLS port."""
    insecure = _ManagedNodeAddress(address="mirror.example.com", port=5600)
    secure = insecure._to_secure()
    
    assert secure._port == 443
    assert secure._address == "mirror.example.com"
    assert secure._is_transport_security() is True

def test_to_secure_already_secure():
    """Test converting already secure address (should be idempotent)."""
    secure = _ManagedNodeAddress(address="127.0.0.1", port=50212)
    result = secure._to_secure()
    
    assert result._port == 50212
    assert result._is_transport_security() is True
    # Should return same instance or equivalent
    assert str(result) == str(secure)

def test_to_secure_custom_port():
    """Test converting address with custom port (should remain unchanged)."""
    custom = _ManagedNodeAddress(address="127.0.0.1", port=9999)
    result = custom._to_secure()
    
    assert result._port == 9999  # Custom port unchanged
    assert result._address == "127.0.0.1"

def test_to_insecure_node_port():
    """Test converting node address from TLS to plaintext port."""
    secure = _ManagedNodeAddress(address="127.0.0.1", port=50212)
    insecure = secure._to_insecure()
    
    assert insecure._port == 50211
    assert insecure._address == "127.0.0.1"
    assert insecure._is_transport_security() is False

def test_to_insecure_mirror_port():
    """Test converting mirror address from TLS to plaintext port."""
    secure = _ManagedNodeAddress(address="mirror.example.com", port=443)
    insecure = secure._to_insecure()
    
    assert insecure._port == 5600
    assert insecure._address == "mirror.example.com"
    assert insecure._is_transport_security() is False

def test_to_insecure_already_insecure():
    """Test converting already insecure address (should be idempotent)."""
    insecure = _ManagedNodeAddress(address="127.0.0.1", port=50211)
    result = insecure._to_insecure()
    
    assert result._port == 50211
    assert result._is_transport_security() is False
    assert str(result) == str(insecure)

def test_to_insecure_custom_port():
    """Test converting address with custom port (should remain unchanged)."""
    custom = _ManagedNodeAddress(address="127.0.0.1", port=9999)
    result = custom._to_insecure()
    
    assert result._port == 9999  # Custom port unchanged
    assert result._address == "127.0.0.1"

def test_get_host_and_port():
    """Test getting host and port components."""
    address = _ManagedNodeAddress(address="example.com", port=50211)
    assert address._get_host() == "example.com"
    assert address._get_port() == 50211 