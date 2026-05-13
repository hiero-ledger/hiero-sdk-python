"""Read-side model for a registered node."""

from __future__ import annotations

from dataclasses import dataclass, field

from hiero_sdk_python.address_book.registered_service_endpoint import RegisteredServiceEndpoint
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services.state.addressbook.registered_node_pb2 import (
    RegisteredNode as RegisteredNodeProto,
)


@dataclass(frozen=True)
class RegisteredNode:
    """Immutable model representing a registered node from network/mirror state."""

    registered_node_id: int
    admin_key: PublicKey | None = None
    description: str | None = None
    service_endpoints: tuple[RegisteredServiceEndpoint, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.registered_node_id, int) or isinstance(self.registered_node_id, bool):
            raise ValueError("registered_node_id must be a positive integer")
        if self.registered_node_id <= 0:
            raise ValueError("registered_node_id must be a positive integer")
        # Ensure service_endpoints is a tuple
        object.__setattr__(self, "service_endpoints", tuple(self.service_endpoints))

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
            registered_node_id=self.registered_node_id,
        )
        if self.admin_key is not None:
            proto.admin_key.CopyFrom(self.admin_key._to_proto())
        if self.description is not None:
            proto.description = self.description
        for ep in self.service_endpoints:
            proto.service_endpoint.append(ep._to_proto())
        return proto

    def __repr__(self) -> str:
        return f"RegisteredNode(registered_node_id={self.registered_node_id}, description={self.description!r})"

    @classmethod
    def _from_dict(cls, data: dict) -> RegisteredNode:
        """Create a RegisteredNode from a mirror-node JSON dict."""
        admin_key: PublicKey | None = None
        admin_key_data = data.get("admin_key")
        if admin_key_data and isinstance(admin_key_data, dict):
            key_type = (admin_key_data.get("_type") or "").upper()
            key_hex = admin_key_data.get("key", "")
            if key_type == "ED25519":
                admin_key = PublicKey.from_string_ed25519(key_hex)
            elif key_type == "ECDSA_SECP256K1":
                admin_key = PublicKey.from_string_ecdsa(key_hex)
            elif key_hex:
                admin_key = PublicKey.from_string(key_hex)

        description: str | None = data.get("description") or None

        endpoints = tuple(RegisteredServiceEndpoint._from_dict(ep) for ep in data.get("service_endpoints", []))

        return cls(
            registered_node_id=data["registered_node_id"],
            admin_key=admin_key,
            description=description,
            service_endpoints=endpoints,
        )
