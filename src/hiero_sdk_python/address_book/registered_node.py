"""Read-side model for a HIP-1137 registered node."""

from __future__ import annotations

from hiero_sdk_python.address_book.registered_service_endpoint import RegisteredServiceEndpoint
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services.state.addressbook.registered_node_pb2 import (
    RegisteredNode as RegisteredNodeProto,
)


class RegisteredNode:
    """Immutable model representing a registered node from network/mirror state."""

    def __init__(
        self,
        registered_node_id: int,
        admin_key: PublicKey | None = None,
        description: str | None = None,
        service_endpoints: tuple[RegisteredServiceEndpoint, ...] = (),
    ) -> None:
        if not isinstance(registered_node_id, int) or isinstance(registered_node_id, bool):
            raise ValueError("registered_node_id must be a positive integer")
        if registered_node_id <= 0:
            raise ValueError("registered_node_id must be a positive integer")

        self._registered_node_id = registered_node_id
        self._admin_key = admin_key
        self._description = description
        self._service_endpoints = tuple(service_endpoints)

    @property
    def registered_node_id(self) -> int:
        return self._registered_node_id

    @property
    def admin_key(self) -> PublicKey | None:
        return self._admin_key

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def service_endpoints(self) -> tuple[RegisteredServiceEndpoint, ...]:
        return self._service_endpoints

    @classmethod
    def _from_proto(cls, proto: RegisteredNodeProto) -> RegisteredNode:
        """Create a RegisteredNode from a protobuf RegisteredNode state message."""
        admin_key: PublicKey | None = None
        if proto.HasField("admin_key"):
            admin_key = PublicKey._from_proto(proto.admin_key)

        description: str | None = proto.description if proto.description else None

        endpoints = tuple(RegisteredServiceEndpoint._from_proto(ep) for ep in proto.service_endpoint)

        return cls(
            registered_node_id=proto.registered_node_id,
            admin_key=admin_key,
            description=description,
            service_endpoints=endpoints,
        )

    def _to_proto(self) -> RegisteredNodeProto:
        """Convert this RegisteredNode to a protobuf RegisteredNode."""
        proto = RegisteredNodeProto(
            registered_node_id=self._registered_node_id,
        )
        if self._admin_key is not None:
            proto.admin_key.CopyFrom(self._admin_key._to_proto())
        if self._description is not None:
            proto.description = self._description
        for ep in self._service_endpoints:
            proto.service_endpoint.append(ep._to_proto())
        return proto

    def __repr__(self) -> str:
        return f"RegisteredNode(registered_node_id={self._registered_node_id}, description={self._description!r})"
