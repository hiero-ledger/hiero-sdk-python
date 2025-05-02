import pytest
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.endpoint import Endpoint
from hiero_sdk_python.address_book.node_address import NodeAddress

pytestmark = pytest.mark.unit

def test_init():
    """Test initialization of _NodeAddress."""
    # Create test data
    account_id = AccountId(0, 0, 123)
    addresses = [Endpoint(address=bytes("192.168.1.1", 'utf-8'), port=8080, domain_name="example.com")]
    cert_hash = b'sample-cert-hash'
    
    # Initialize _NodeAddress
    node_address = NodeAddress(
        public_key="sample-public-key",
        account_id=account_id,
        node_id=1234,
        cert_hash=cert_hash,
        addresses=addresses,
        description="Sample Node"
    )
    
    # Assert properties are set correctly
    assert node_address._public_key == "sample-public-key"
    assert node_address._account_id == account_id
    assert node_address._node_id == 1234
    assert node_address._cert_hash == cert_hash
    assert node_address._addresses == addresses
    assert node_address._description == "Sample Node"

def test_string_representation():
    """Test string representation of _NodeAddress."""
    # Create AccountId
    account_id = AccountId(0, 0, 123)
    
    # Create    
    endpoint = Endpoint(address=bytes("192.168.1.1", 'utf-8'), port=8080, domain_name="example.com")
    
    # Create NodeAddress
    node_address = NodeAddress(
        public_key="sample-public-key",
        account_id=account_id,
        node_id=1234,
        cert_hash=b'sample-cert-hash',
        addresses=[endpoint],
        description="Sample Node"
    )
    
    # Get string representation
    result = str(node_address)
    
    # Check if expected fields are in the result
    assert "NodeAccountId: 0.0.123" in result
    assert "CertHash: 73616d706c652d636572742d68617368" in result  # hex representation of sample-cert-hash
    assert "NodeId: 1234" in result
    assert "PubKey: sample-public-key" in result