"""
NodeDeleteTransaction class.
"""

from typing import Optional

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.node_delete_pb2 import NodeDeleteTransactionBody
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.transaction.transaction import Transaction


class NodeDeleteTransaction(Transaction):
    """
    Represents a node delete transaction on the network.

    This transaction deletes an existing node on the network with the specified node ID.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a node delete transaction.
    """

    def __init__(self, node_id: Optional[int] = None):
        """
        Initializes a new NodeDeleteTransaction instance with the specified parameters.

        Args:
            node_id (Optional[int]):
                The parameters for the node delete transaction.
        """
        super().__init__()
        self.node_id: Optional[int] = node_id

    def set_node_id(self, node_id: Optional[int]) -> "NodeDeleteTransaction":
        """
        Sets the node id for this node delete transaction.

        Args:
            node_id (Optional[int]):
                The node id of the node.

        Returns:
            NodeDeleteTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.node_id = node_id
        return self

    def _build_proto_body(self) -> NodeDeleteTransactionBody:
        """
        Returns the protobuf body for the node delete transaction.

        Returns:
            NodeDeleteTransactionBody: The protobuf body for this transaction.

        Raises:
            ValueError: If node_id is not set.
        """
        if self.node_id is None:
            raise ValueError("Missing required NodeID")

        return NodeDeleteTransactionBody(
            node_id=self.node_id,
        )

    def build_transaction_body(self) -> TransactionBody:
        """
        Builds the transaction body for node delete transaction.

        Returns:
            TransactionBody: The built transaction body.

        Raises:
            ValueError: If node_id is not set.
        """
        node_delete_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.nodeDelete.CopyFrom(node_delete_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for node delete transaction.

        Returns:
            NodeDeleteTransactionBody: The built scheduled transaction body.
        """
        node_delete_body = self._build_proto_body()
        scheduled_body = self.build_base_scheduled_body()
        scheduled_body.nodeDelete.CopyFrom(node_delete_body)
        return scheduled_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the node delete transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: An object containing the transaction function to delete a node.
        """
        return _Method(
            transaction_func=channel.address_book.deleteNode, query_func=None
        )
