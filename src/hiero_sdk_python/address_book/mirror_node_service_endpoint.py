"""Registered mirror node service endpoint."""

from __future__ import annotations

from dataclasses import dataclass

from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
)
from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


@dataclass(eq=True)
class MirrorNodeServiceEndpoint(RegisteredServiceEndpoint):
    """A registered endpoint for a mirror node service."""

    def _endpoint_type_proto(self) -> dict[str, RegisteredServiceEndpointProto.MirrorNodeEndpoint]:
        """Return the protobuf mirror-node subtype."""
        return {"mirror_node": RegisteredServiceEndpointProto.MirrorNodeEndpoint()}

    @classmethod
    def _from_proto(cls, proto: RegisteredServiceEndpointProto) -> MirrorNodeServiceEndpoint:
        """Build a mirror node endpoint from protobuf."""
        return cls(**cls._base_kwargs_from_proto(proto))
