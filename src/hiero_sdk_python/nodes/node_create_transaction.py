"""
NodeCreateTransaction class.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.endpoint import Endpoint
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.node_create_pb2 import NodeCreateTransactionBody
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)


@dataclass
class NodeCreateParams:
    """
    Represents node attributes that can be set on creation.

    Attributes:
        account_id (Optional[AccountId]): The account ID of the node.
        description (Optional[str]): The description of the node.
        gossip_endpoints (List[Endpoint]): The gossip endpoints of the node.
        service_endpoints (List[Endpoint]): The service endpoints of the node.
        gossip_ca_certificate (Optional[bytes]): The gossip ca certificate of the node.
        grpc_certificate_hash (Optional[bytes]): The grpc certificate hash of the node.
        admin_key (Optional[PublicKey]): The admin key of the node.
        decline_reward (Optional[bool]): The decline reward of the node.
        grpc_web_proxy_endpoint (Optional[Endpoint]): The grpc web proxy endpoint of the node.
    """

    account_id: Optional[AccountId] = None
    description: Optional[str] = None
    gossip_endpoints: List[Endpoint] = field(default_factory=list)
    service_endpoints: List[Endpoint] = field(default_factory=list)
    gossip_ca_certificate: Optional[bytes] = None
    grpc_certificate_hash: Optional[bytes] = None
    admin_key: Optional[PublicKey] = None
    decline_reward: Optional[bool] = None
    grpc_web_proxy_endpoint: Optional[Endpoint] = None


class NodeCreateTransaction(Transaction):
    """
    Represents a node create transaction on the network.

    This transaction creates a new node on the network with the specified account ID,
    description, endpoints, certificates, admin key, and other node properties.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a node create transaction.
    """

    def __init__(self, node_create_params: Optional[NodeCreateParams] = None):
        """
        Initializes a new NodeCreateTransaction instance with the specified parameters.

        Args:
            node_create_params (Optional[NodeCreateParams]):
                The parameters for the node create transaction.
        """
        super().__init__()
        node_create_params = node_create_params or NodeCreateParams()
        self.account_id: Optional[AccountId] = node_create_params.account_id
        self.description: Optional[str] = node_create_params.description
        self.gossip_endpoints: List[Endpoint] = node_create_params.gossip_endpoints
        self.service_endpoints: List[Endpoint] = node_create_params.service_endpoints
        self.gossip_ca_certificate: Optional[bytes] = (
            node_create_params.gossip_ca_certificate
        )
        self.grpc_certificate_hash: Optional[bytes] = (
            node_create_params.grpc_certificate_hash
        )
        self.admin_key: Optional[PublicKey] = node_create_params.admin_key
        self.decline_reward: Optional[bool] = node_create_params.decline_reward
        self.grpc_web_proxy_endpoint: Optional[Endpoint] = (
            node_create_params.grpc_web_proxy_endpoint
        )

    def set_account_id(self, account_id: Optional[AccountId]) -> "NodeCreateTransaction":
        """
        Sets the account id for this node create transaction.

        Args:
            account_id (AccountId):
                The account id of the node.

        Returns:
            NodeCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.account_id = account_id
        return self

    def set_description(self, description: Optional[str]) -> "NodeCreateTransaction":
        """
        Sets the description for this node create transaction.

        Args:
            description (str):
                The description of the node.

        Returns:
            NodeCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.description = description
        return self

    def set_gossip_endpoints(
        self, gossip_endpoints: Optional[List[Endpoint]]
    ) -> "NodeCreateTransaction":
        """
        Sets the gossip endpoints for this node create transaction.

        Args:
            gossip_endpoints (List[Endpoint]):
                The gossip endpoints of the node.

        Returns:
            NodeCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.gossip_endpoints = gossip_endpoints
        return self

    def set_service_endpoints(
        self, service_endpoints: Optional[List[Endpoint]]
    ) -> "NodeCreateTransaction":
        """
        Sets the service endpoints for this node create transaction.

        Args:
            service_endpoints (List[Endpoint]):
                The service endpoints of the node.

        Returns:
            NodeCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.service_endpoints = service_endpoints
        return self

    def set_gossip_ca_certificate(
        self, gossip_ca_certificate: Optional[bytes]
    ) -> "NodeCreateTransaction":
        """
        Sets the gossip ca certificate for this node create transaction.

        Args:
            gossip_ca_certificate (bytes):
                The gossip ca certificate of the node.

        Returns:
            NodeCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.gossip_ca_certificate = gossip_ca_certificate
        return self

    def set_grpc_certificate_hash(
        self, grpc_certificate_hash: Optional[bytes]
    ) -> "NodeCreateTransaction":
        """
        Sets the grpc certificate hash for this node create transaction.

        Args:
            grpc_certificate_hash (bytes):
                The grpc certificate hash of the node.

        Returns:
            NodeCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.grpc_certificate_hash = grpc_certificate_hash
        return self

    def set_admin_key(self, admin_key: Optional[PublicKey]) -> "NodeCreateTransaction":
        """
        Sets the admin key for this node create transaction.

        Args:
            admin_key (PublicKey):
                The admin key of the node.

        Returns:
            NodeCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.admin_key = admin_key
        return self

    def set_decline_reward(
        self, decline_reward: Optional[bool]
    ) -> "NodeCreateTransaction":
        """
        Sets the decline reward for this node create transaction.

        Args:
            decline_reward (bool):
                The decline reward of the node.

        Returns:
            NodeCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.decline_reward = decline_reward
        return self

    def set_grpc_web_proxy_endpoint(
        self, grpc_web_proxy_endpoint: Optional[Endpoint]
    ) -> "NodeCreateTransaction":
        """
        Sets the grpc web proxy endpoint for this node create transaction.

        Args:
            grpc_web_proxy_endpoint (Endpoint):
                The grpc web proxy endpoint of the node.

        Returns:
            NodeCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.grpc_web_proxy_endpoint = grpc_web_proxy_endpoint
        return self

    def _build_proto_body(self) -> NodeCreateTransactionBody:
        """
        Returns the protobuf body for the node create transaction.

        Returns:
            NodeCreateTransactionBody: The protobuf body for this transaction.
        """
        return NodeCreateTransactionBody(
            account_id=self.account_id._to_proto() if self.account_id else None,
            description=self.description,
            gossip_endpoint=[
                endpoint._to_proto() for endpoint in self.gossip_endpoints or []
            ],
            service_endpoint=[
                endpoint._to_proto() for endpoint in self.service_endpoints or []
            ],
            gossip_ca_certificate=self.gossip_ca_certificate,
            grpc_certificate_hash=self.grpc_certificate_hash,
            admin_key=self.admin_key._to_proto() if self.admin_key else None,
            decline_reward=self.decline_reward,
            grpc_proxy_endpoint=(
                self.grpc_web_proxy_endpoint._to_proto()
                if self.grpc_web_proxy_endpoint
                else None
            ),
        )

    def build_transaction_body(self) -> TransactionBody:
        """
        Builds the transaction body for node create transaction.

        Returns:
            TransactionBody: The built transaction body.
        """
        node_create_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.nodeCreate.CopyFrom(node_create_body)
        return transaction_body
    
    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for node create transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        node_create_body = self._build_proto_body()
        scheduled_body = self.build_base_scheduled_body()
        scheduled_body.nodeCreate.CopyFrom(node_create_body)
        return scheduled_body


    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the node create transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: An object containing the transaction function to create a node.
        """
        return _Method(transaction_func=channel.address_book.createNode, query_func=None)
