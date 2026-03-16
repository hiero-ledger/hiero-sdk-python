"""RegisteredNodeCreateTransaction class."""

from __future__ import annotations

from dataclasses import dataclass, field

from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
)
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.registered_node_create_pb2 import (
    RegisteredNodeCreateTransactionBody,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.utils.key_utils import (
    Key,
    contains_empty_key_list,
    key_from_proto,
    key_to_proto,
)


@dataclass
class RegisteredNodeCreateParams:
    """Fields supported by a registered node create transaction."""

    admin_key: Key | None = None
    description: str | None = None
    service_endpoints: list[RegisteredServiceEndpoint] = field(default_factory=list)


class RegisteredNodeCreateTransaction(Transaction):
    """Create a registered node in the address book."""

    MAX_DESCRIPTION_BYTES = 100

    def __init__(self, registered_node_create_params: RegisteredNodeCreateParams | None = None) -> None:
        """Initialize a registered node create transaction."""
        super().__init__()
        registered_node_create_params = registered_node_create_params or RegisteredNodeCreateParams()
        self.admin_key = registered_node_create_params.admin_key
        self.description = registered_node_create_params.description
        self.service_endpoints = list(registered_node_create_params.service_endpoints)

    def set_admin_key(self, admin_key: Key | None) -> RegisteredNodeCreateTransaction:
        """Set the registered node admin key."""
        self._require_not_frozen()
        self.admin_key = admin_key
        return self

    def set_description(self, description: str | None) -> RegisteredNodeCreateTransaction:
        """Set the registered node description."""
        self._require_not_frozen()
        self.description = description
        return self

    def set_service_endpoints(
        self, service_endpoints: list[RegisteredServiceEndpoint] | None
    ) -> RegisteredNodeCreateTransaction:
        """Replace the registered node service endpoints."""
        self._require_not_frozen()
        self.service_endpoints = list(service_endpoints or [])
        return self

    def add_service_endpoint(self, service_endpoint: RegisteredServiceEndpoint) -> RegisteredNodeCreateTransaction:
        """Append a service endpoint."""
        self._require_not_frozen()
        self.service_endpoints.append(service_endpoint)
        return self

    def _validate(self) -> None:
        """Validate the transaction fields."""
        if self.admin_key is None:
            raise ValueError("Missing required admin_key")
        if contains_empty_key_list(self.admin_key):
            raise ValueError("admin_key must not contain an empty KeyList.")
        if not self.service_endpoints:
            raise ValueError("At least one service endpoint is required.")
        if len(self.service_endpoints) > 50:
            raise ValueError("A maximum of 50 service endpoints is allowed.")
        if self.description is not None and len(self.description.encode("utf-8")) > self.MAX_DESCRIPTION_BYTES:
            raise ValueError("Description must not exceed 100 UTF-8 bytes.")

    def _build_proto_body(self) -> RegisteredNodeCreateTransactionBody:
        """Build the protobuf body for the registered node create transaction."""
        self._validate()
        return RegisteredNodeCreateTransactionBody(
            admin_key=key_to_proto(self.admin_key),
            description=self.description,
            service_endpoint=[endpoint._to_proto() for endpoint in self.service_endpoints],
        )

    def build_transaction_body(self) -> TransactionBody:
        """Build the transaction body."""
        registered_node_create_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.registeredNodeCreate.CopyFrom(registered_node_create_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """Build the scheduled transaction body."""
        registered_node_create_body = self._build_proto_body()
        scheduled_body = self.build_base_scheduled_body()
        scheduled_body.registeredNodeCreate.CopyFrom(registered_node_create_body)
        return scheduled_body

    def _get_method(self, channel: _Channel) -> _Method:
        """Return the gRPC method for execution."""
        return _Method(
            transaction_func=channel.address_book.createRegisteredNode,
            query_func=None,
        )

    @classmethod
    def _from_protobuf(cls, transaction_body, body_bytes: bytes, sig_map):
        """Restore a registered node create transaction from protobuf."""
        transaction = super()._from_protobuf(transaction_body, body_bytes, sig_map)
        if transaction_body.HasField("registeredNodeCreate"):
            create_body = transaction_body.registeredNodeCreate
            transaction.admin_key = key_from_proto(create_body.admin_key) if create_body.HasField("admin_key") else None
            transaction.description = create_body.description or None
            transaction.service_endpoints = [
                RegisteredServiceEndpoint._from_proto(endpoint_proto) for endpoint_proto in create_body.service_endpoint
            ]
        return transaction
