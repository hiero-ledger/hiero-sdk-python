"""Registered RPC relay service endpoint."""

from __future__ import annotations

from dataclasses import dataclass

from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
)
from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


@dataclass(eq=True)
class RpcRelayServiceEndpoint(RegisteredServiceEndpoint):
    """A registered endpoint for an RPC relay service."""

    def _endpoint_type_proto(self) -> dict[str, RegisteredServiceEndpointProto.RpcRelayEndpoint]:
        """Return the protobuf RPC relay subtype."""
        return {"rpc_relay": RegisteredServiceEndpointProto.RpcRelayEndpoint()}

    @classmethod
    def _from_proto(cls, proto: RegisteredServiceEndpointProto) -> RpcRelayServiceEndpoint:
        """Build an RPC relay endpoint from protobuf."""
        return cls(**cls._base_kwargs_from_proto(proto))
