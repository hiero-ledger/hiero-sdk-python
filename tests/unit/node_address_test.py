from platform import node
import pytest
import binascii
import pytest
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.endpoint import Endpoint
from hiero_sdk_python.address_book.node_address import NodeAddress
from hiero_sdk_python.hapi.services.basic_types_pb2 import NodeAddress as NodeAddressProto
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


def test_to_proto():
    """Test conversion of NodeAddress to protobuf with endpoints."""
    account_id = AccountId(0, 0, 123)
    endpoint = Endpoint(
        address=bytes("192.168.1.1", "utf-8"),
        port=8080,
        domain_name="example.com"
    )
    node_address = NodeAddress(
        public_key="sample-public-key",
        account_id=account_id,
        node_id=1234,
        cert_hash=b"sample-cert-hash",
        addresses=[endpoint],
        description="Sample Node"
    )

    node_address_proto = node_address._to_proto()

    # Scalars
    assert node_address_proto.RSA_PubKey == "sample-public-key"
    assert node_address_proto.nodeId == 1234
    assert node_address_proto.nodeCertHash == b"sample-cert-hash"
    assert node_address_proto.description == "Sample Node"

    # AccountId
    assert node_address_proto.nodeAccountId.shardNum == 0
    assert node_address_proto.nodeAccountId.realmNum == 0
    assert node_address_proto.nodeAccountId.accountNum == 123

    # ServiceEndpoint
    assert len(node_address_proto.serviceEndpoint) == 1
    ep = node_address_proto.serviceEndpoint[0]
    assert ep.ipAddressV4 == bytes("192.168.1.1", "utf-8")
    assert ep.port == 8080
    assert ep.domain_name == "example.com"


def test_from_dict():
    """Test creation of NodeAddress from a dictionary with hex cert hash."""
    node_dict = {
        "public_key": "sample-public-key",
        "node_account_id": "0.0.123",
        "node_id": 1234,
        "node_cert_hash": binascii.hexlify(b"sample-cert-hash").decode("utf-8"),
        "description": "Sample Node",
        "service_endpoints": [
            {"ip_address_v4": "192.168.1.1", "port": 8080, "domain_name": "example.com"}
        ],
    }

    # Create NodeAddress from dict
    node_address = NodeAddress._from_dict(node_dict)

    assert node_address._public_key == "sample-public-key"
    assert node_address._account_id == AccountId.from_string("0.0.123")
    assert node_address._node_id == 1234
    assert node_address._cert_hash == b"sample-cert-hash"
    assert node_address._description == "Sample Node"
    assert len(node_address._addresses) == 1


def test_from_proto():
    """Test creation of NodeAddress from protobuf with endpoint."""
    account_id_proto = AccountId(0, 0, 123)._to_proto()
    endpoint_proto = Endpoint(
        address=bytes("192.168.1.1", "utf-8"),
        port=8080,
        domain_name="example.com"
    )._to_proto()

    # Create NodeAddressProto
    node_address_proto = NodeAddressProto(
        RSA_PubKey="sample-public-key",
        nodeAccountId=account_id_proto,
        nodeId=1234,
        nodeCertHash=b"sample-cert-hash",
        description="Sample Node",
    )
    node_address_proto.serviceEndpoint.append(endpoint_proto)

    node_address = NodeAddress._from_proto(node_address_proto)

    assert node_address._public_key == "sample-public-key"
    assert node_address._account_id == AccountId(0, 0, 123)
    assert node_address._node_id == 1234
    assert node_address._cert_hash == b"sample-cert-hash"
    assert node_address._description == "Sample Node"
    assert len(node_address._addresses) == 1


def test_round_trip():
    """Ensure NodeAddress → Proto → NodeAddress round trip works."""
    account_id = AccountId(0, 0, 123)
    endpoint = Endpoint(
        address=bytes("192.168.1.1", "utf-8"),
        port=8080,
        domain_name="example.com"
    )

    # Create NodeAddress
    node_address = NodeAddress(
        public_key="sample-public-key",
        account_id=account_id,
        node_id=1234,
        cert_hash=b"sample-cert-hash",
        addresses=[endpoint],
        description="Sample Node"
    )

    # Convert to proto
    proto = node_address._to_proto()
    # Convert back from proto
    node_address2 = NodeAddress._from_proto(proto)

    # Assert all fields are equal
    assert node_address._public_key == node_address2._public_key
    assert node_address._account_id == node_address2._account_id
    assert node_address._node_id == node_address2._node_id
    assert node_address._cert_hash == node_address2._cert_hash
    assert node_address._description == node_address2._description


def test_empty_addresses():
    """Test NodeAddress with no endpoints produces empty serviceEndpoint."""
    node_address = NodeAddress(
        public_key="sample-public-key",
        account_id=AccountId(0, 0, 123),
        node_id=1234,
        cert_hash=b"sample-cert-hash",
        addresses=[],
        description="No endpoints"
    )

    proto = node_address._to_proto()
    assert len(proto.serviceEndpoint) == 0
