"""Unit tests for registered service endpoint types."""

from __future__ import annotations

import pytest

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import (
    BlockNodeServiceEndpoint,
)
from hiero_sdk_python.address_book.general_service_endpoint import (
    GeneralServiceEndpoint,
)
from hiero_sdk_python.address_book.mirror_node_service_endpoint import (
    MirrorNodeServiceEndpoint,
)
from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
)
from hiero_sdk_python.address_book.rpc_relay_service_endpoint import (
    RpcRelayServiceEndpoint,
)
from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


pytestmark = pytest.mark.unit


def _supports_general_service_endpoint() -> bool:
    """Return whether this protobuf build includes the general endpoint subtype."""
    endpoint_type_oneof = RegisteredServiceEndpointProto.DESCRIPTOR.oneofs_by_name.get("endpoint_type")
    if endpoint_type_oneof is None:
        return False

    return any(
        field.message_type is not None and "General" in field.message_type.name for field in endpoint_type_oneof.fields
    )


def test_block_node_service_endpoint_roundtrip():
    """Block node endpoints should round-trip through protobuf."""
    endpoint = BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        requires_tls=True,
        endpoint_api=BlockNodeApi.STATE_PROOF,
    )

    proto = endpoint._to_proto()
    roundtrip = RegisteredServiceEndpoint._from_proto(proto)

    assert isinstance(roundtrip, BlockNodeServiceEndpoint)
    assert roundtrip == endpoint


def test_mirror_node_service_endpoint_roundtrip():
    """Mirror node endpoints should round-trip through protobuf."""
    endpoint = MirrorNodeServiceEndpoint(ip_address=b"\x7f\x00\x00\x01", port=5600)

    proto = endpoint._to_proto()
    roundtrip = RegisteredServiceEndpoint._from_proto(proto)

    assert isinstance(roundtrip, MirrorNodeServiceEndpoint)
    assert roundtrip == endpoint


def test_rpc_relay_service_endpoint_roundtrip():
    """RPC relay endpoints should round-trip through protobuf."""
    endpoint = RpcRelayServiceEndpoint(domain_name="relay.example.com", port=7545)

    proto = endpoint._to_proto()
    roundtrip = RegisteredServiceEndpoint._from_proto(proto)

    assert isinstance(roundtrip, RpcRelayServiceEndpoint)
    assert roundtrip == endpoint


def test_general_service_endpoint_roundtrip():
    """General service endpoints should round-trip when supported by protobuf."""
    if not _supports_general_service_endpoint():
        pytest.skip("General service endpoint is unavailable in this protobuf version.")

    endpoint = GeneralServiceEndpoint(
        domain_name="general.example.com",
        port=443,
        requires_tls=True,
        description="General node service",
    )

    proto = endpoint._to_proto()
    roundtrip = RegisteredServiceEndpoint._from_proto(proto)

    assert isinstance(roundtrip, GeneralServiceEndpoint)
    assert roundtrip == endpoint


def test_registered_service_endpoint_requires_exactly_one_address():
    """Endpoints must use either an IP address or a domain name."""
    with pytest.raises(ValueError, match="Exactly one of ip_address or domain_name must be set."):
        MirrorNodeServiceEndpoint(
            ip_address=b"\x7f\x00\x00\x01",
            domain_name="mirror.example.com",
            port=5600,
        )

    with pytest.raises(ValueError, match="Exactly one of ip_address or domain_name must be set."):
        RpcRelayServiceEndpoint(port=7545)


def test_registered_service_endpoint_validates_port_range():
    """Endpoints should reject invalid port values."""
    with pytest.raises(ValueError, match="port must be between 0 and 65535."):
        BlockNodeServiceEndpoint(
            domain_name="block.example.com",
            port=70000,
            endpoint_api=BlockNodeApi.STATUS,
        )


def test_registered_service_endpoint_rejects_invalid_ip_address():
    """Endpoints should reject malformed packed IP addresses."""
    with pytest.raises(ValueError, match="ip_address must be a valid packed IPv4 or IPv6 address."):
        MirrorNodeServiceEndpoint(ip_address=b"\x7f\x00\x00", port=5600)


def test_registered_service_endpoint_rejects_invalid_domain_name():
    """Endpoints should reject malformed domain names."""
    with pytest.raises(ValueError, match="domain_name must not exceed 250 ASCII characters."):
        RpcRelayServiceEndpoint(domain_name="a" * 251, port=7545)

    with pytest.raises(ValueError, match="domain_name must contain only ASCII characters."):
        RpcRelayServiceEndpoint(domain_name="murror.exämple.com", port=7545)

    with pytest.raises(ValueError, match="domain_name must be a valid domain name."):
        RpcRelayServiceEndpoint(domain_name="-invalid.example.com", port=7545)
