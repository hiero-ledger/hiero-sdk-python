"""Registered block node service endpoint."""

from __future__ import annotations

from dataclasses import dataclass

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
)
from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


@dataclass(eq=True)
class BlockNodeServiceEndpoint(RegisteredServiceEndpoint):
    """A registered endpoint for a block node service."""

    endpoint_api: BlockNodeApi = BlockNodeApi.OTHER

    def __post_init__(self) -> None:
        """Normalize the enum value before base validation."""
        self.endpoint_api = BlockNodeApi(self.endpoint_api)
        super().__post_init__()

    def _endpoint_type_proto(self) -> dict[str, RegisteredServiceEndpointProto.BlockNodeEndpoint]:
        """Return the protobuf block-node subtype."""
        return {"block_node": RegisteredServiceEndpointProto.BlockNodeEndpoint(endpoint_api=int(self.endpoint_api))}

    @classmethod
    def _from_proto(cls, proto: RegisteredServiceEndpointProto) -> BlockNodeServiceEndpoint:
        """Build a block node endpoint from protobuf."""
        return cls(
            endpoint_api=BlockNodeApi(proto.block_node.endpoint_api),
            **cls._base_kwargs_from_proto(proto),
        )
