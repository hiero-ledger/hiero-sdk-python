from typing import List, TypedDict

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.endpoint import Endpoint, EndpointDict
from hiero_sdk_python.hapi.services.basic_types_pb2 import NodeAddress as NodeAddressProto

class NodeDict(TypedDict):
    """
    A TypedDict representing the structure of a node address in JSON format.
    
    Attributes:
        public_key (str): The RSA public key of the node.
        node_account_id (str): The account ID of the node in 'shard.realm.num' format.
        node_id (int): The node ID.
        node_cert_hash (str): The node certificate hash in hexadecimal format.
        service_endpoints (list[EndpointDict]): List of service endpoints for the node.
        description (str): Description of the node.
    """
    public_key: str
    node_account_id: str
    node_id: int
    node_cert_hash: str
    service_endpoints: List[EndpointDict]
    description: str

class NodeAddress:
    """
    Represents the address of a node on the Hedera network.
    """
    
    def __init__(
        self,
        public_key: str = None,
        account_id: AccountId = None,
        node_id: int = None,
        cert_hash: bytes = None,
        addresses: List[Endpoint] = None,
        description: str = None
    ):
        """
        Initialize a new NodeAddress instance.
        
        Args:
            public_key (str, optional): The RSA public key of the node.
            account_id (AccountId, optional): The account ID of the node.
            node_id (int, optional): The node ID.
            cert_hash (bytes, optional): The node certificate hash.
            addresses (list[Endpoint], optional): List of endpoints for the node.
            description (str, optional): Description of the node.
        """
        self._public_key: str = public_key
        self._account_id: AccountId = account_id
        self._node_id: int = node_id
        self._cert_hash: bytes = cert_hash
        self._addresses: List[Endpoint] = addresses
        self._description: str = description
    
    @classmethod
    def _from_proto(cls, node_address_proto: NodeAddressProto) -> "NodeAddress":
        """
        Create a NodeAddress from a protobuf NodeAddress.
        
        Args:
            node_address_proto: The protobuf NodeAddress object.
            
        Returns:
            NodeAddress: A new NodeAddress instance.
        """
        addresses: List[Endpoint] = []
        
        for endpoint_proto in node_address_proto.serviceEndpoint:
            addresses.append(Endpoint._from_proto(endpoint_proto))
        
        account_id: AccountId = None
        if node_address_proto.nodeAccountId:
            account_id = AccountId._from_proto(node_address_proto.nodeAccountId)
        
        return cls(
            public_key=node_address_proto.RSA_PubKey,
            account_id=account_id,
            node_id=node_address_proto.nodeId,
            cert_hash=node_address_proto.nodeCertHash,
            addresses=addresses,
            description=node_address_proto.description
        )
    
    def _to_proto(self):
        """
        Convert this NodeAddress to a protobuf NodeAddress.
        
        Returns:
            NodeAddressProto: A protobuf NodeAddress object.
        """
        node_address_proto = NodeAddressProto(
            RSA_PubKey=self._public_key,
            nodeId=self._node_id,
            nodeCertHash=self._cert_hash,
            description=self._description
        )
        
        if self._account_id:
            node_address_proto.nodeAccountId.CopyFrom(self._account_id._to_proto())
        
        service_endpoints: List[Endpoint] = []
        for endpoint in self._addresses:
            service_endpoints.append(endpoint._to_proto())
        
        node_address_proto.serviceEndpoint = service_endpoints
        
        return node_address_proto
    
    def __str__(self):
        """
        Get a string representation of the NodeAddress.
        
        Returns:
            str: The string representation of the NodeAddress.
        """
        addresses_str: str = ""
        for address in self._addresses:
            addresses_str += str(address)
        cert_hash_str: str = self._cert_hash.hex()
        node_id_str: str = str(self._node_id)
        account_id_str: str = str(self._account_id)
        
        return (
            f"NodeAccountId: {account_id_str} {addresses_str}\n"
            f"CertHash: {cert_hash_str}\n"
            f"NodeId: {node_id_str}\n"
            f"PubKey: {self._public_key or ''}"
        )

    @classmethod
    def _from_dict(cls, node: NodeDict) -> 'NodeAddress':
        """
        Create a NodeAddress from a dictionary.
        """
        
        service_endpoints: List[EndpointDict] = node.get('service_endpoints', [])
        public_key: str = node.get('public_key')
        account_id: AccountId = AccountId.from_string(node.get('node_account_id'))
        node_id: int = node.get('node_id')
        # Get the hash from the node, remove the 0x prefix and convert to bytes
        cert_hash: bytes = bytes.fromhex(node.get('node_cert_hash').removeprefix('0x'))
        description: str = node.get('description')
        
        endpoints: List[Endpoint] = []
        for endpoint in service_endpoints:
            endpoints.append(Endpoint.from_dict(endpoint))
        
        return cls(
            public_key=public_key,
            account_id=account_id,
            node_id=node_id,
            cert_hash=cert_hash,
            description=description,
            addresses=endpoints
        )
