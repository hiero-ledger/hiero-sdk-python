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
