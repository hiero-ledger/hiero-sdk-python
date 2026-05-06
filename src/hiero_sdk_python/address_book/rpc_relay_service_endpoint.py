from __future__ import annotations

from hiero_sdk_python.address_book.registered_service_endpoint import RegisteredServiceEndpoint
from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


class RpcRelayServiceEndpoint(RegisteredServiceEndpoint):
    """A registered service endpoint for an RPC relay."""

    def _set_endpoint_type(self, proto: RegisteredServiceEndpointProto) -> None:
        proto.rpc_relay.SetInParent()
