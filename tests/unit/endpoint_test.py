import pytest
from unittest.mock import MagicMock
from src.hiero_sdk_python.address_book.endpoint import Endpoint

pytestmark = pytest.mark.unit

def test_getter_setter():

    """Test for Endpoint constructor, getters, and setters with fluent interface."""
 
    endpoint = Endpoint(address=None, port=None, domain_name=None)
    
    # Test fluent interface (method chaining)
    result = endpoint.set_address(b'127.0.1.1')
    assert result is endpoint, "set_address should return self for method chaining"
    
    result = endpoint.set_port(77777)
    assert result is endpoint, "set_port should return self for method chaining"
    
    result = endpoint.set_domain_name("redpanda.com")
    assert result is endpoint, "set_domain_name should return self for method chaining"
 
    # Protect against breaking changes - verify attributes exist
    assert hasattr(endpoint, 'get_address'), "Missing get_address method"
    assert hasattr(endpoint, 'get_port'), "Missing get_port method"
    assert hasattr(endpoint, 'get_domain_name'), "Missing get_domain_name method"
    
    assert endpoint.get_address() == b'127.0.1.1'
    assert endpoint.get_port() == 77777
    assert endpoint.get_domain_name() == "redpanda.com"


def test_constructor_with_values():
    """Test Endpoint constructor with actual values."""
    endpoint = Endpoint(address=b'192.168.1.1', port=8080, domain_name="example.com")
    # Protect against breaking changes
    assert isinstance(endpoint, Endpoint), "Constructor must return Endpoint instance"
    assert endpoint.get_address() == b'192.168.1.1'
    assert endpoint.get_port() == 8080
    assert endpoint.get_domain_name() == "example.com"


@pytest.mark.parametrize(
    ("input_port", "expected_port"),
    [
        (0, 50211),
        (50111, 50211),
        (80, 80),
    ],
)
def test_from_proto_port_mapping(input_port, expected_port):
    """Tests port mapping logic when converting Protobuf ServiceEndpoint to Endpoint.
    
    Port mapping rules:
    - Port 0 or 50111 maps to 50211 (legacy/default behavior)
    - Other ports pass through unchanged
    """
     
    mock_proto = MagicMock()
    mock_proto.port = input_port
    mock_proto.ipAddressV4 = b"127.0.1.1"
    mock_proto.domain_name = "redpanda.com"
     
    endpoint = Endpoint._from_proto(mock_proto)
    
    # Verify port mapping
    assert endpoint.get_port() == expected_port
    
    # Verify all fields are mapped correctly (not just port)
    assert endpoint.get_address() == b"127.0.1.1", "Address must be mapped from proto"
    assert endpoint.get_domain_name() == "redpanda.com", "Domain name must be mapped from proto"
    
    # Protect against breaking changes - PRIORITY 1
    assert isinstance(endpoint, Endpoint), "Must return Endpoint instance"

def test_to_proto():

    """Verifies that an Endpoint instance can be correctly serialized back into 
    a Protobuf ServiceEndpoint object with all fields intact."""

    endpoint = Endpoint(address=b'127.0.1.1', port=77777, domain_name="redpanda.com")
    proto = endpoint._to_proto()
    assert proto.ipAddressV4 == b'127.0.1.1'
    assert proto.port == 77777
    assert proto.domain_name == "redpanda.com"

def test_str():

    """Tests the human-readable string representation of the Endpoint."""

    endpoint = Endpoint(address=b'127.0.1.1', port=77777, domain_name="redpanda.com")
    result = str(endpoint)
    
    # Verify return type
    assert isinstance(result, str), "String representation should return a string"
    assert result == '127.0.1.1:77777'


def test_str_with_none_values():
    """Test string representation when address or port is None."""
    endpoint = Endpoint(address=None, port=None, domain_name="example.com")
    with pytest.raises(AttributeError):
        str(endpoint)

@pytest.mark.parametrize("invalid_data", [
    {"port": 77777, "domain_name": "test.com"},
    {"ip_address_v4": "127.0.0.1", "domain_name": "test.com"},
    {"ip_address_v4": "127.0.0.1", "port": 77777},
])
def test_from_dict_missing_fields(invalid_data):
    """Test that from_dict raises ValueError when required fields are missing."""
    with pytest.raises(ValueError, match="JSON data must contain"):
        Endpoint.from_dict(invalid_data)

def test_from_dict_error():

    """Validates 'Guard Clause' error handling"""
    
    invalid_data = {"port": 77777}
    with pytest.raises(ValueError, match="JSON data must contain"):
        Endpoint.from_dict(invalid_data)

def test_from_dict_success():
    """ Tests successful creation of an Endpoint from a dictionary (JSON format) """
    data = {
        "ip_address_v4": "127.0.0.1",
        "port": 77777,
        "domain_name": "redpanda.com"
    }
    endpoint = Endpoint.from_dict(data)
    
    assert endpoint.get_address() == b"127.0.0.1"
    assert endpoint.get_port() == 77777
    assert endpoint.get_domain_name() == "redpanda.com"