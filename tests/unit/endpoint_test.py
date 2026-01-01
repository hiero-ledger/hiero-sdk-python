import pytest
from unittest.mock import MagicMock
from src.hiero_sdk_python.address_book.endpoint import Endpoint

pytestmark = pytest.mark.unit

def test_getter_setter():

    ''' Test for Endpoint constructor'''

    endpoint = Endpoint(address=None, port=None, domain_name=None)
    endpoint.set_address(b'127.0.1.1')
    endpoint.set_port(77777)
    endpoint.set_domain_name("redpanda.com")

    assert endpoint.get_address() == b'127.0.1.1'
    assert endpoint.get_port() == 77777
    assert endpoint.get_domain_name() == "redpanda.com"

@pytest.mark.parametrize("input_port, expected_port", [
    (0, 50211),      
    (50111, 50211),  
    (80, 80)         
])

def test_from_proto_port_mapping(input_port, expected_port):

    ''' Tests the logic that converts a Protobuf ServiceEndpoint into an Endpoint object.'''
    
    mock_proto = MagicMock()
    mock_proto.port = input_port
    mock_proto.ipAddressV4 = b"127.0.1.1"
    mock_proto.domain_name = "redpanda.com"
    
    endpoint = Endpoint._from_proto(mock_proto)
    assert endpoint.get_port() == expected_port

def test_to_proto():

    '''Verifies that an Endpoint instance can be correctly serialized back into 
    a Protobuf ServiceEndpoint object with all fields intact.'''

    endpoint = Endpoint(address=b'127.0.1.1', port=77777, domain_name="redpanda.com")
    proto = endpoint._to_proto()
    assert proto.ipAddressV4 == b'127.0.1.1'
    assert proto.port == 77777
    assert proto.domain_name == "redpanda.com"

def test_str():

    ''' Tests the human-readable string representation of the Endpoint. '''

    endpoint = Endpoint(address=b'127.0.1.1', port=77777, domain_name="redpanda.com")
    assert str(endpoint) == '127.0.1.1:77777'

def test_from_dict_error():

    '''Validates 'Guard Clause' error handling'''
    
    invalid_data = {"port": 77777}
    with pytest.raises(ValueError, match="JSON data must contain"):
        Endpoint.from_dict(invalid_data)

def test_from_dict_success():
    ''' Tests successful creation of an Endpoint from a dictionary (JSON format) '''
    data = {
        "ip_address_v4": "127.0.0.1",
        "port": 77777,
        "domain_name": "redpanda.com"
    }
    endpoint = Endpoint.from_dict(data)
    
    assert endpoint.get_address() == b"127.0.0.1"
    assert endpoint.get_port() == 77777
    assert endpoint.get_domain_name() == "redpanda.com"