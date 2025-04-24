from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.endpoint import Endpoint
from hiero_sdk_python.hapi.services.basic_types_pb2 import NodeAddress as NodeAddressProto


class NodeAddress:
    """
    Represents the address of a node on the Hedera network.
    """
    
    def __init__(
        self,
        public_key=None,
        account_id=None,
        node_id=None,
        cert_hash=None,
        addresses=None,
        description=None
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
        self._public_key : str = public_key
        self._account_id : AccountId = account_id
        self._node_id : int = node_id
        self._cert_hash : bytes = cert_hash
        self._addresses : list[Endpoint] = addresses
        self._description : str = description
    
    @classmethod
    def _from_proto(cls, node_address_proto : 'NodeAddressProto'):
        """
        Create a NodeAddress from a protobuf NodeAddress.
        
        Args:
            node_address_proto: The protobuf NodeAddress object.
            
        Returns:
            NodeAddress: A new NodeAddress instance.
        """
        addresses = []
        
        for endpoint_proto in node_address_proto.serviceEndpoint:
            addresses.append(Endpoint.from_proto(endpoint_proto))
        
        account_id = None
        if node_address_proto.nodeAccountId:
            account_id = AccountId.from_proto(node_address_proto.nodeAccountId)
        
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
            node_address_proto.nodeAccountId.CopyFrom(self._account_id.to_proto())
        
        service_endpoints = []
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
        addresses_str = ""
        for address in self._addresses:
            addresses_str += address.__str__()
        
        cert_hash_str = self._cert_hash.hex()
        node_id_str = str(self._node_id)
        account_id_str = self._account_id.__str__()
        
        return (
            f"NodeAccountId: {account_id_str} {addresses_str}\n"
            f"CertHash: {cert_hash_str}\n"
            f"NodeId: {node_id_str}\n"
            f"PubKey: {self._public_key or ''}"
        )
