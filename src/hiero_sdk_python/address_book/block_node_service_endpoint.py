from __future__ import annotations

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.registered_service_endpoint import RegisteredServiceEndpoint
from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


class BlockNodeServiceEndpoint(RegisteredServiceEndpoint):
    """A registered service endpoint for a block node."""

    def __init__(
        self,
        ip_address: bytes | None = None,
        domain_name: str | None = None,
        port: int = 0,
        requires_tls: bool = False,
        endpoint_apis: list[BlockNodeApi] | None = None,
    ) -> None:
        super().__init__(ip_address=ip_address, domain_name=domain_name, port=port, requires_tls=requires_tls)
        if endpoint_apis is None or len(endpoint_apis) == 0:
            raise ValueError("endpoint_apis must be non-empty")
        for api in endpoint_apis:
            if isinstance(api, bool):
                raise TypeError("endpoint_apis values must be BlockNodeApi, not bool")
        self.endpoint_apis: list[BlockNodeApi] = [BlockNodeApi(api) for api in endpoint_apis]

    def _set_endpoint_type(self, proto: RegisteredServiceEndpointProto) -> None:
        block_node = proto.block_node
        for api in self.endpoint_apis:
            block_node.endpoint_api.append(api.value)

    @classmethod
    def _from_proto_inner(
        cls,
        proto: RegisteredServiceEndpointProto,
        ip_address: bytes | None,
        domain_name: str | None,
        port: int,
        requires_tls: bool,
    ) -> BlockNodeServiceEndpoint:
        apis = [BlockNodeApi(v) for v in proto.block_node.endpoint_api]
        if not apis:
            apis = [BlockNodeApi.OTHER]
        return cls(
            ip_address=ip_address,
            domain_name=domain_name,
            port=port,
            requires_tls=requires_tls,
            endpoint_apis=apis,
        )
