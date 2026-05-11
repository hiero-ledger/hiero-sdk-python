"""RegisteredNodeUpdateTransaction class."""

from __future__ import annotations

from google.protobuf.wrappers_pb2 import StringValue

from hiero_sdk_python.address_book.registered_service_endpoint import RegisteredServiceEndpoint
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.registered_node_update_pb2 import RegisteredNodeUpdateTransactionBody
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.transaction.transaction import Transaction


class RegisteredNodeUpdateTransaction(Transaction):
    """Updates an existing registered node on the network."""

    def __init__(self):
        super().__init__()
        self.registered_node_id: int | None = None
        self.admin_key: PublicKey | None = None
        self.description: str | None = None
        self.service_endpoints: list[RegisteredServiceEndpoint] | None = None

    def set_registered_node_id(self, registered_node_id: int | None) -> RegisteredNodeUpdateTransaction:
        """Sets the registered node ID to update.

        Args:
            registered_node_id: The ID of the registered node to update.

        Returns:
            RegisteredNodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.registered_node_id = registered_node_id
        return self

    def set_admin_key(self, admin_key: PublicKey | None) -> RegisteredNodeUpdateTransaction:
        """Sets the new admin key for the registered node.

        Args:
            admin_key: The new admin key, or None to leave unchanged.

        Returns:
            RegisteredNodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.admin_key = admin_key
        return self

    def set_description(self, description: str | None) -> RegisteredNodeUpdateTransaction:
        """Sets the new description for the registered node.

        Args:
            description: The new description, or None to leave unchanged.

        Returns:
            RegisteredNodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.description = description
        return self

    def set_service_endpoints(
        self, service_endpoints: list[RegisteredServiceEndpoint] | None
    ) -> RegisteredNodeUpdateTransaction:
        """Sets the new service endpoints for the registered node.

        Args:
            service_endpoints: The new service endpoints, or None to leave unchanged.

        Returns:
            RegisteredNodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.service_endpoints = service_endpoints
        return self

    def add_service_endpoint(self, endpoint: RegisteredServiceEndpoint) -> RegisteredNodeUpdateTransaction:
        """Adds a service endpoint to the registered node.

        Args:
            endpoint: The service endpoint to add.

        Returns:
            RegisteredNodeUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        if self.service_endpoints is None:
            self.service_endpoints = []
        self.service_endpoints.append(endpoint)
        return self

    def _build_proto_body(self) -> RegisteredNodeUpdateTransactionBody:
        body = RegisteredNodeUpdateTransactionBody(
            registered_node_id=self.registered_node_id,
            admin_key=self.admin_key._to_proto() if self.admin_key else None,
            description=(StringValue(value=self.description) if self.description is not None else None),
        )
        if self.service_endpoints is not None:
            for ep in self.service_endpoints:
                body.service_endpoint.append(ep._to_proto())
        return body

    def build_transaction_body(self) -> TransactionBody:
        body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.registeredNodeUpdate.CopyFrom(body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        body = self._build_proto_body()
        scheduled_body = self.build_base_scheduled_body()
        scheduled_body.registeredNodeUpdate.CopyFrom(body)
        return scheduled_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(transaction_func=channel.address_book.updateRegisteredNode, query_func=None)

    @classmethod
    def _from_protobuf(cls, transaction_body, body_bytes: bytes, sig_map):
        transaction = super()._from_protobuf(transaction_body, body_bytes, sig_map)

        if transaction_body.HasField("registeredNodeUpdate"):
            pb = transaction_body.registeredNodeUpdate
            transaction.registered_node_id = pb.registered_node_id
            if pb.HasField("admin_key"):
                transaction.admin_key = PublicKey._from_proto(pb.admin_key)
            if pb.HasField("description"):
                transaction.description = pb.description.value
            if pb.service_endpoint:
                transaction.service_endpoints = [
                    RegisteredServiceEndpoint._from_proto(ep) for ep in pb.service_endpoint
                ]

        return transaction
