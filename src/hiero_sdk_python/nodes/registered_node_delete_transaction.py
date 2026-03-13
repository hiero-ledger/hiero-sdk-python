"""RegisteredNodeDeleteTransaction class."""

from __future__ import annotations

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.registered_node_delete_pb2 import (
    RegisteredNodeDeleteTransactionBody,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.transaction.transaction import Transaction


class RegisteredNodeDeleteTransaction(Transaction):
    """Delete an existing registered node."""

    def __init__(self, registered_node_id: int | None = None) -> None:
        """Initialize a registered node delete transaction."""
        super().__init__()
        self.registered_node_id = registered_node_id

    def set_registered_node_id(self, registered_node_id: int | None) -> RegisteredNodeDeleteTransaction:
        """Set the registered node id."""
        self._require_not_frozen()
        self.registered_node_id = registered_node_id
        return self

    def _build_proto_body(self) -> RegisteredNodeDeleteTransactionBody:
        """Build the protobuf body."""
        if self.registered_node_id is None:
            raise ValueError("Missing required RegisteredNodeID")

        return RegisteredNodeDeleteTransactionBody(registered_node_id=self.registered_node_id)

    def build_transaction_body(self) -> TransactionBody:
        """Build the transaction body."""
        registered_node_delete_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.registeredNodeDelete.CopyFrom(registered_node_delete_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """Build the scheduled transaction body."""
        registered_node_delete_body = self._build_proto_body()
        scheduled_body = self.build_base_scheduled_body()
        scheduled_body.registeredNodeDelete.CopyFrom(registered_node_delete_body)
        return scheduled_body

    def _get_method(self, channel: _Channel) -> _Method:
        """Return the gRPC method for execution."""
        return _Method(
            transaction_func=channel.address_book.deleteRegisteredNode,
            query_func=None,
        )

    @classmethod
    def _from_protobuf(cls, transaction_body, body_bytes: bytes, sig_map):
        """Restore a registered node delete transaction from protobuf."""
        transaction = super()._from_protobuf(transaction_body, body_bytes, sig_map)
        if transaction_body.HasField("registeredNodeDelete"):
            transaction.registered_node_id = transaction_body.registeredNodeDelete.registered_node_id
        return transaction
