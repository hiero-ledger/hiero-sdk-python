from __future__ import annotations

from hiero_sdk_python.address_book.registered_service_endpoint import RegisteredServiceEndpoint
from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


class RpcRelayServiceEndpoint(RegisteredServiceEndpoint):
    """A registered service endpoint for an RPC relay."""

    def _set_endpoint_type(self, proto: RegisteredServiceEndpointProto) -> None:
        proto.rpc_relay.SetInParent()

    @classmethod
    def _from_proto_inner(
        cls,
        _proto: RegisteredServiceEndpointProto,
        ip_address: bytes | None,
        domain_name: str | None,
        port: int,
        requires_tls: bool,
    ) -> RpcRelayServiceEndpoint:
        return cls(
            ip_address=ip_address,
            domain_name=domain_name,
            port=port,
            requires_tls=requires_tls,
        )
