from __future__ import annotations

from hiero_sdk_python.address_book.registered_service_endpoint import RegisteredServiceEndpoint
from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


class MirrorNodeServiceEndpoint(RegisteredServiceEndpoint):
    """A registered service endpoint for a mirror node."""

    def _set_endpoint_type(self, proto: RegisteredServiceEndpointProto) -> None:
        # Accessing the field initializes the oneof to mirror_node
        proto.mirror_node.SetInParent()

    @classmethod
    def _from_proto_inner(
        cls,
        _proto: RegisteredServiceEndpointProto,
        ip_address: bytes | None,
        domain_name: str | None,
        port: int,
        requires_tls: bool,
    ) -> MirrorNodeServiceEndpoint:
        return cls(
            ip_address=ip_address,
            domain_name=domain_name,
            port=port,
            requires_tls=requires_tls,
        )
