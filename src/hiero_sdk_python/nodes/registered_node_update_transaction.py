"""RegisteredNodeUpdateTransaction class."""

from __future__ import annotations

from dataclasses import dataclass, field

from google.protobuf.wrappers_pb2 import StringValue

from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
)
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.registered_node_update_pb2 import (
    RegisteredNodeUpdateTransactionBody,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.transaction.transaction import Transaction


@dataclass
class RegisteredNodeUpdateParams:
    """Fields supported by a registered node update transaction."""

    registered_node_id: int | None = None
    admin_key: PublicKey | None = None
    description: str | None = None
    service_endpoints: list[RegisteredServiceEndpoint] = field(default_factory=list)


class RegisteredNodeUpdateTransaction(Transaction):
    """Update an existing registered node."""

    def __init__(self, registered_node_update_params: RegisteredNodeUpdateParams | None = None) -> None:
        """Initialize a registered node update transaction."""
        super().__init__()
        registered_node_update_params = registered_node_update_params or RegisteredNodeUpdateParams()
        self.registered_node_id = registered_node_update_params.registered_node_id
        self.admin_key = registered_node_update_params.admin_key
        self.description = registered_node_update_params.description
        self.service_endpoints = list(registered_node_update_params.service_endpoints)

    def set_registered_node_id(self, registered_node_id: int | None) -> RegisteredNodeUpdateTransaction:
        """Set the registered node id."""
        self._require_not_frozen()
        self.registered_node_id = registered_node_id
        return self

    def set_admin_key(self, admin_key: PublicKey | None) -> RegisteredNodeUpdateTransaction:
        """Set the registered node admin key."""
        self._require_not_frozen()
        self.admin_key = admin_key
        return self

    def set_description(self, description: str | None) -> RegisteredNodeUpdateTransaction:
        """Set the registered node description."""
        self._require_not_frozen()
        self.description = description
        return self

    def set_service_endpoints(
        self, service_endpoints: list[RegisteredServiceEndpoint] | None
    ) -> RegisteredNodeUpdateTransaction:
        """Replace the registered node service endpoints."""
        self._require_not_frozen()
        self.service_endpoints = list(service_endpoints or [])
        return self

    def add_service_endpoint(self, service_endpoint: RegisteredServiceEndpoint) -> RegisteredNodeUpdateTransaction:
        """Append a service endpoint."""
        self._require_not_frozen()
        self.service_endpoints.append(service_endpoint)
        return self

    def _validate(self) -> None:
        """Validate the transaction fields."""
        if self.registered_node_id is None:
            raise ValueError("Missing required RegisteredNodeID")
        if len(self.service_endpoints) > 50:
            raise ValueError("A maximum of 50 service endpoints is allowed.")

    def _build_proto_body(self) -> RegisteredNodeUpdateTransactionBody:
        """Build the protobuf body for the registered node update transaction."""
        self._validate()
        return RegisteredNodeUpdateTransactionBody(
            registered_node_id=self.registered_node_id,
            admin_key=self.admin_key._to_proto() if self.admin_key else None,
            description=(StringValue(value=self.description) if self.description is not None else None),
            service_endpoint=[endpoint._to_proto() for endpoint in self.service_endpoints],
        )

    def build_transaction_body(self) -> TransactionBody:
        """Build the transaction body."""
        registered_node_update_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.registeredNodeUpdate.CopyFrom(registered_node_update_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """Build the scheduled transaction body."""
        registered_node_update_body = self._build_proto_body()
        scheduled_body = self.build_base_scheduled_body()
        scheduled_body.registeredNodeUpdate.CopyFrom(registered_node_update_body)
        return scheduled_body

    def _get_method(self, channel: _Channel) -> _Method:
        """Return the gRPC method for execution."""
        return _Method(
            transaction_func=channel.address_book.updateRegisteredNode,
            query_func=None,
        )

    @classmethod
    def _from_protobuf(cls, transaction_body, body_bytes: bytes, sig_map):
        """Restore a registered node update transaction from protobuf."""
        transaction = super()._from_protobuf(transaction_body, body_bytes, sig_map)
        if transaction_body.HasField("registeredNodeUpdate"):
            update_body = transaction_body.registeredNodeUpdate
            transaction.registered_node_id = update_body.registered_node_id
            transaction.admin_key = (
                PublicKey._from_proto(update_body.admin_key) if update_body.HasField("admin_key") else None
            )
            transaction.description = update_body.description.value if update_body.HasField("description") else None
            transaction.service_endpoints = [
                RegisteredServiceEndpoint._from_proto(endpoint_proto) for endpoint_proto in update_body.service_endpoint
            ]
        return transaction
