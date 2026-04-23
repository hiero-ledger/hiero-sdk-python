"""Block node endpoint API values."""

from __future__ import annotations

from enum import IntEnum

from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


class BlockNodeApi(IntEnum):
    """Well-known block node APIs."""

    OTHER = RegisteredServiceEndpointProto.BlockNodeEndpoint.OTHER
    STATUS = RegisteredServiceEndpointProto.BlockNodeEndpoint.STATUS
    PUBLISH = RegisteredServiceEndpointProto.BlockNodeEndpoint.PUBLISH
    SUBSCRIBE_STREAM = RegisteredServiceEndpointProto.BlockNodeEndpoint.SUBSCRIBE_STREAM
    STATE_PROOF = RegisteredServiceEndpointProto.BlockNodeEndpoint.STATE_PROOF
