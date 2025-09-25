"""
NodeUpdateTransaction class.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional

from google.protobuf.wrappers_pb2 import BoolValue, BytesValue, StringValue

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.endpoint import Endpoint
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.node_update_pb2 import NodeUpdateTransactionBody
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.transaction.transaction import Transaction


@dataclass
class NodeUpdateParams:
    """
    Represents node attributes that can be set on update.

    Attributes:
        node_id (Optional[int]): The node ID of the node.
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

    node_id: Optional[int] = None
    account_id: Optional[AccountId] = None
    description: Optional[str] = None
    gossip_endpoints: List[Endpoint] = field(default_factory=list)
    service_endpoints: List[Endpoint] = field(default_factory=list)
    gossip_ca_certificate: Optional[bytes] = None
    grpc_certificate_hash: Optional[bytes] = None
    admin_key: Optional[PublicKey] = None
    decline_reward: Optional[bool] = None
    grpc_web_proxy_endpoint: Optional[Endpoint] = None


class NodeUpdateTransaction(Transaction):
    """
    Represents a node update transaction on the network.

    This transaction updates an existing node on the network with the specified account ID,
    description, endpoints, certificates, admin key, and other node properties.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a node update transaction.
    """

    def __init__(self, node_update_params: Optional[NodeUpdateParams] = None):
        """
        Initializes a new NodeUpdateTransaction instance with the specified parameters.

        Args:
            node_update_params (Optional[NodeUpdateParams]):
                The parameters for the node update transaction.
        """
        super().__init__()
        node_update_params = node_update_params or NodeUpdateParams()
        self.node_id: Optional[int] = node_update_params.node_id
        self.account_id: Optional[AccountId] = node_update_params.account_id
        self.description: Optional[str] = node_update_params.description
        self.gossip_endpoints: List[Endpoint] = node_update_params.gossip_endpoints
        self.service_endpoints: List[Endpoint] = node_update_params.service_endpoints
        self.gossip_ca_certificate: Optional[bytes] = (
            node_update_params.gossip_ca_certificate
        )
        self.grpc_certificate_hash: Optional[bytes] = (
            node_update_params.grpc_certificate_hash
        )
        self.admin_key: Optional[PublicKey] = node_update_params.admin_key
        self.decline_reward: Optional[bool] = node_update_params.decline_reward
        self.grpc_web_proxy_endpoint: Optional[Endpoint] = (
            node_update_params.grpc_web_proxy_endpoint
        )

    def set_node_id(self, node_id: Optional[int]) -> "NodeUpdateTransaction":
        """
        Sets the node id for this node update transaction.

        Args:
            node_id (Optional[int]):
                The node id of the node.

        Returns:
            NodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.node_id = node_id
        return self

    def set_account_id(self, account_id: Optional[AccountId]) -> "NodeUpdateTransaction":
        """
        Sets the account id for this node update transaction.

        Args:
            account_id (AccountId):
                The account id of the node.

        Returns:
            NodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.account_id = account_id
        return self

    def set_description(self, description: Optional[str]) -> "NodeUpdateTransaction":
        """
        Sets the description for this node update transaction.

        Args:
            description (str):
                The description of the node.

        Returns:
            NodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.description = description
        return self

    def set_gossip_endpoints(
        self, gossip_endpoints: Optional[List[Endpoint]]
    ) -> "NodeUpdateTransaction":
        """
        Sets the gossip endpoints for this node update transaction.

        Args:
            gossip_endpoints (List[Endpoint]):
                The gossip endpoints of the node.

        Returns:
            NodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.gossip_endpoints = gossip_endpoints
        return self

    def set_service_endpoints(
        self, service_endpoints: Optional[List[Endpoint]]
    ) -> "NodeUpdateTransaction":
        """
        Sets the service endpoints for this node update transaction.

        Args:
            service_endpoints (List[Endpoint]):
                The service endpoints of the node.

        Returns:
            NodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.service_endpoints = service_endpoints
        return self

    def set_gossip_ca_certificate(
        self, gossip_ca_certificate: Optional[bytes]
    ) -> "NodeUpdateTransaction":
        """
        Sets the gossip ca certificate for this node update transaction.

        Args:
            gossip_ca_certificate (bytes):
                The gossip ca certificate of the node.

        Returns:
            NodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.gossip_ca_certificate = gossip_ca_certificate
        return self

    def set_grpc_certificate_hash(
        self, grpc_certificate_hash: Optional[bytes]
    ) -> "NodeUpdateTransaction":
        """
        Sets the grpc certificate hash for this node update transaction.

        Args:
            grpc_certificate_hash (bytes):
                The grpc certificate hash of the node.

        Returns:
            NodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.grpc_certificate_hash = grpc_certificate_hash
        return self

    def set_admin_key(self, admin_key: Optional[PublicKey]) -> "NodeUpdateTransaction":
        """
        Sets the admin key for this node update transaction.

        Args:
            admin_key (PublicKey):
                The admin key of the node.

        Returns:
            NodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.admin_key = admin_key
        return self

    def set_decline_reward(
        self, decline_reward: Optional[bool]
    ) -> "NodeUpdateTransaction":
        """
        Sets the decline reward for this node update transaction.

        Args:
            decline_reward (bool):
                The decline reward of the node.

        Returns:
            NodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.decline_reward = decline_reward
        return self

    def set_grpc_web_proxy_endpoint(
        self, grpc_web_proxy_endpoint: Optional[Endpoint]
    ) -> "NodeUpdateTransaction":
        """
        Sets the grpc web proxy endpoint for this node update transaction.

        Args:
            grpc_web_proxy_endpoint (Endpoint):
                The grpc web proxy endpoint of the node.

        Returns:
            NodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.grpc_web_proxy_endpoint = grpc_web_proxy_endpoint
        return self

    def _convert_to_proto(self, obj: Optional[Any]) -> Any:
        """Convert object to proto if it exists, otherwise return None"""
        return obj._to_proto() if obj else None

    def _convert_to_proto_list(self, obj: Optional[List[Any]]) -> Any:
        """Convert list of objects to proto if it exists, otherwise return empty list"""
        return [obj._to_proto() for obj in obj or []]

    def _build_proto_body(self) -> NodeUpdateTransactionBody:
        """
        Returns the protobuf body for the node update transaction.

        Returns:
            NodeUpdateTransactionBody: The protobuf body for this transaction.
        """
        return NodeUpdateTransactionBody(
            node_id=self.node_id,
            account_id=self._convert_to_proto(self.account_id),
            description=(
                StringValue(value=self.description)
                if self.description is not None
                else None
            ),
            gossip_endpoint=self._convert_to_proto_list(self.gossip_endpoints),
            service_endpoint=self._convert_to_proto_list(self.service_endpoints),
            gossip_ca_certificate=(
                BytesValue(value=self.gossip_ca_certificate)
                if self.gossip_ca_certificate is not None
                else None
            ),
            grpc_certificate_hash=(
                BytesValue(value=self.grpc_certificate_hash)
                if self.grpc_certificate_hash is not None
                else None
            ),
            admin_key=self._convert_to_proto(self.admin_key),
            decline_reward=(
                BoolValue(value=self.decline_reward)
                if self.decline_reward is not None
                else None
            ),
            grpc_proxy_endpoint=self._convert_to_proto(self.grpc_web_proxy_endpoint),
        )

    def build_transaction_body(self) -> TransactionBody:
        """
        Builds the transaction body for node update transaction.

        Returns:
            TransactionBody: The built transaction body.
        """
        node_update_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.nodeUpdate.CopyFrom(node_update_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for node update transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        node_update_body = self._build_proto_body()
        scheduled_body = self.build_base_scheduled_body()
        scheduled_body.nodeUpdate.CopyFrom(node_update_body)
        return scheduled_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the node update transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: An object containing the transaction function to update a node.
        """
        return _Method(transaction_func=channel.address_book.updateNode, query_func=None)
