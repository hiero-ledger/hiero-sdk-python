"""RegisteredNodeCreateTransaction class."""

from __future__ import annotations

from hiero_sdk_python.address_book.registered_service_endpoint import RegisteredServiceEndpoint
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.registered_node_create_pb2 import RegisteredNodeCreateTransactionBody
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.transaction.transaction import Transaction


class RegisteredNodeCreateTransaction(Transaction):
    """Creates a new registered node on the network."""

    def __init__(self):
        super().__init__()
        self.admin_key: Key | None = None
        self.description: str | None = None
        self.service_endpoints: list[RegisteredServiceEndpoint] = []

    def set_admin_key(self, admin_key: Key | None) -> RegisteredNodeCreateTransaction:
        """Sets the admin key for the registered node.

        Args:
            admin_key: The admin key, or None to clear.

        Returns:
            RegisteredNodeCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.admin_key = admin_key
        return self

    def set_description(self, description: str | None) -> RegisteredNodeCreateTransaction:
        """Sets the description for the registered node.

        Args:
            description: The description, or None to clear.

        Returns:
            RegisteredNodeCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.description = description
        return self

    def set_service_endpoints(
        self, service_endpoints: list[RegisteredServiceEndpoint]
    ) -> RegisteredNodeCreateTransaction:
        """Sets the service endpoints for the registered node.

        Args:
            service_endpoints: The list of service endpoints.

        Returns:
            RegisteredNodeCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.service_endpoints = service_endpoints
        return self

    def add_service_endpoint(self, endpoint: RegisteredServiceEndpoint) -> RegisteredNodeCreateTransaction:
        """Adds a service endpoint to the registered node.

        Args:
            endpoint: The service endpoint to add.

        Returns:
            RegisteredNodeCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.service_endpoints.append(endpoint)
        return self

    def _build_proto_body(self) -> RegisteredNodeCreateTransactionBody:
        return RegisteredNodeCreateTransactionBody(
            admin_key=self.admin_key.to_proto_key() if self.admin_key else None,
            description=self.description or "",
            service_endpoint=[ep._to_proto() for ep in self.service_endpoints],
        )

    def build_transaction_body(self) -> TransactionBody:
        body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.registeredNodeCreate.CopyFrom(body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        body = self._build_proto_body()
        scheduled_body = self.build_base_scheduled_body()
        scheduled_body.registeredNodeCreate.CopyFrom(body)
        return scheduled_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(transaction_func=channel.address_book.createRegisteredNode, query_func=None)

    @classmethod
    def _from_protobuf(cls, transaction_body):
        transaction = super()._from_protobuf(transaction_body)

        if transaction_body.HasField("registeredNodeCreate"):
            pb = transaction_body.registeredNodeCreate
            if pb.HasField("admin_key"):
                transaction.admin_key = Key.from_proto_key(pb.admin_key)
            if pb.description:
                transaction.description = pb.description
            transaction.service_endpoints = [RegisteredServiceEndpoint._from_proto(ep) for ep in pb.service_endpoint]

        return transaction
