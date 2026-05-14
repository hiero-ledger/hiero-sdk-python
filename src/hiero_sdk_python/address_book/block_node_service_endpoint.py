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
        self.endpoint_apis: list[BlockNodeApi] = [BlockNodeApi(api) for api in (endpoint_apis or [])]

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

    @classmethod
    def _from_dict_inner(cls, type_data: dict, **base_kwargs) -> BlockNodeServiceEndpoint:
        """Build from the ``block_node`` sub-dict of a mirror-node JSON endpoint."""
        raw_apis = type_data.get("endpoint_apis") or []
        apis = [BlockNodeApi[a.upper()] if isinstance(a, str) else BlockNodeApi(a) for a in raw_apis]
        return cls(endpoint_apis=apis, **base_kwargs)
