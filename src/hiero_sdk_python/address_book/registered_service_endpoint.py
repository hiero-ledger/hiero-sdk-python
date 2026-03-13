"""Base type for registered service endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


@dataclass(eq=True)
class RegisteredServiceEndpoint:
    """Shared fields for a registered node service endpoint."""

    ip_address: bytes | None = None
    domain_name: str | None = None
    port: int = 0
    requires_tls: bool = False

    def __post_init__(self) -> None:
        """Validate fields after dataclass initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate the common endpoint fields."""
        has_ip_address = self.ip_address is not None
        has_domain_name = self.domain_name is not None

        if has_ip_address == has_domain_name:
            raise ValueError("Exactly one of ip_address or domain_name must be set.")

        if not 0 <= self.port <= 65535:
            raise ValueError("port must be between 0 and 65535.")

    @classmethod
    def _base_kwargs_from_proto(cls, proto: RegisteredServiceEndpointProto) -> dict[str, Any]:
        """Extract the common constructor kwargs from protobuf."""
        address_type = proto.WhichOneof("address")
        if address_type == "ip_address":
            return {
                "ip_address": proto.ip_address,
                "domain_name": None,
                "port": proto.port,
                "requires_tls": proto.requires_tls,
            }

        if address_type == "domain_name":
            return {
                "ip_address": None,
                "domain_name": proto.domain_name,
                "port": proto.port,
                "requires_tls": proto.requires_tls,
            }

        raise ValueError("Registered service endpoint address is required.")

    def _endpoint_type_proto(self) -> dict[str, Any]:
        """Return the endpoint-type-specific protobuf field."""
        raise NotImplementedError("Subclasses must implement _endpoint_type_proto().")

    def _to_proto(self) -> RegisteredServiceEndpointProto:
        """Convert the endpoint to protobuf."""
        proto_kwargs = {
            "port": self.port,
            "requires_tls": self.requires_tls,
            **self._endpoint_type_proto(),
        }

        if self.ip_address is not None:
            proto_kwargs["ip_address"] = self.ip_address
        else:
            proto_kwargs["domain_name"] = self.domain_name

        return RegisteredServiceEndpointProto(**proto_kwargs)

    @classmethod
    def _from_proto(cls, proto: RegisteredServiceEndpointProto) -> RegisteredServiceEndpoint:
        """Build the concrete endpoint type from protobuf."""
        endpoint_type = proto.WhichOneof("endpoint_type")

        if endpoint_type == "block_node":
            from hiero_sdk_python.address_book.block_node_service_endpoint import (
                BlockNodeServiceEndpoint,
            )

            return BlockNodeServiceEndpoint._from_proto(proto)

        if endpoint_type == "mirror_node":
            from hiero_sdk_python.address_book.mirror_node_service_endpoint import (
                MirrorNodeServiceEndpoint,
            )

            return MirrorNodeServiceEndpoint._from_proto(proto)

        if endpoint_type == "rpc_relay":
            from hiero_sdk_python.address_book.rpc_relay_service_endpoint import (
                RpcRelayServiceEndpoint,
            )

            return RpcRelayServiceEndpoint._from_proto(proto)

        raise ValueError("Registered service endpoint type is required.")
