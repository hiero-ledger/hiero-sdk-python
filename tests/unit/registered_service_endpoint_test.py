from __future__ import annotations

import pytest

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
from hiero_sdk_python.address_book.general_service_endpoint import GeneralServiceEndpoint
from hiero_sdk_python.address_book.mirror_node_service_endpoint import MirrorNodeServiceEndpoint
from hiero_sdk_python.address_book.registered_service_endpoint import RegisteredServiceEndpoint
from hiero_sdk_python.address_book.rpc_relay_service_endpoint import RpcRelayServiceEndpoint
from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


pytestmark = pytest.mark.unit


# --- BlockNodeApi ---


class TestBlockNodeApi:
    def test_enum_values_match_protobuf(self):
        """BlockNodeApi numeric values must match generated protobuf enum."""
        proto_enum = RegisteredServiceEndpointProto.BlockNodeEndpoint.BlockNodeApi
        assert proto_enum.Value("OTHER") == BlockNodeApi.OTHER
        assert proto_enum.Value("STATUS") == BlockNodeApi.STATUS
        assert proto_enum.Value("PUBLISH") == BlockNodeApi.PUBLISH
        assert proto_enum.Value("SUBSCRIBE_STREAM") == BlockNodeApi.SUBSCRIBE_STREAM
        assert proto_enum.Value("STATE_PROOF") == BlockNodeApi.STATE_PROOF


# --- BlockNodeServiceEndpoint ---


class TestBlockNodeServiceEndpoint:
    def test_round_trip_ip_address(self):
        ep = BlockNodeServiceEndpoint(
            ip_address=b"\xc0\xa8\x01\x01",
            port=8080,
            requires_tls=True,
            endpoint_apis=[BlockNodeApi.PUBLISH],
        )
        proto = ep._to_proto()
        restored = RegisteredServiceEndpoint._from_proto(proto)
        assert isinstance(restored, BlockNodeServiceEndpoint)
        assert restored.ip_address == b"\xc0\xa8\x01\x01"
        assert restored.domain_name is None
        assert restored.port == 8080
        assert restored.requires_tls is True
        assert restored.endpoint_apis == [BlockNodeApi.PUBLISH]

    def test_round_trip_domain_name(self):
        ep = BlockNodeServiceEndpoint(
            domain_name="block.example.com",
            port=443,
            requires_tls=True,
            endpoint_apis=[BlockNodeApi.STATUS],
        )
        proto = ep._to_proto()
        restored = RegisteredServiceEndpoint._from_proto(proto)
        assert isinstance(restored, BlockNodeServiceEndpoint)
        assert restored.domain_name == "block.example.com"
        assert restored.ip_address is None
        assert restored.port == 443
        assert restored.requires_tls is True

    def test_multiple_endpoint_apis(self):
        apis = [BlockNodeApi.PUBLISH, BlockNodeApi.SUBSCRIBE_STREAM, BlockNodeApi.STATE_PROOF]
        ep = BlockNodeServiceEndpoint(
            ip_address=b"\x7f\x00\x00\x01",
            port=9090,
            requires_tls=False,
            endpoint_apis=apis,
        )
        proto = ep._to_proto()
        restored = RegisteredServiceEndpoint._from_proto(proto)
        assert isinstance(restored, BlockNodeServiceEndpoint)
        assert restored.endpoint_apis == apis

    def test_empty_endpoint_apis_raises(self):
        with pytest.raises(ValueError, match="endpoint_apis must be non-empty"):
            BlockNodeServiceEndpoint(
                ip_address=b"\x7f\x00\x00\x01",
                port=80,
                endpoint_apis=[],
            )

    def test_none_endpoint_apis_raises(self):
        with pytest.raises(ValueError, match="endpoint_apis must be non-empty"):
            BlockNodeServiceEndpoint(
                ip_address=b"\x7f\x00\x00\x01",
                port=80,
                endpoint_apis=None,
            )


# --- MirrorNodeServiceEndpoint ---


class TestMirrorNodeServiceEndpoint:
    def test_round_trip(self):
        ep = MirrorNodeServiceEndpoint(
            ip_address=b"\x0a\x00\x00\x01",
            port=5600,
            requires_tls=False,
        )
        proto = ep._to_proto()
        restored = RegisteredServiceEndpoint._from_proto(proto)
        assert isinstance(restored, MirrorNodeServiceEndpoint)
        assert restored.ip_address == b"\x0a\x00\x00\x01"
        assert restored.port == 5600
        assert restored.requires_tls is False


# --- RpcRelayServiceEndpoint ---


class TestRpcRelayServiceEndpoint:
    def test_round_trip(self):
        ep = RpcRelayServiceEndpoint(
            domain_name="relay.example.com",
            port=7546,
            requires_tls=True,
        )
        proto = ep._to_proto()
        restored = RegisteredServiceEndpoint._from_proto(proto)
        assert isinstance(restored, RpcRelayServiceEndpoint)
        assert restored.domain_name == "relay.example.com"
        assert restored.port == 7546
        assert restored.requires_tls is True


# --- GeneralServiceEndpoint ---


class TestGeneralServiceEndpoint:
    def test_round_trip_with_description(self):
        ep = GeneralServiceEndpoint(
            ip_address=b"\xc0\xa8\x00\x01",
            port=3000,
            requires_tls=False,
            description="My custom service",
        )
        proto = ep._to_proto()
        restored = RegisteredServiceEndpoint._from_proto(proto)
        assert isinstance(restored, GeneralServiceEndpoint)
        assert restored.description == "My custom service"
        assert restored.ip_address == b"\xc0\xa8\x00\x01"
        assert restored.port == 3000

    def test_round_trip_without_description(self):
        ep = GeneralServiceEndpoint(
            domain_name="general.example.com",
            port=8080,
            requires_tls=True,
            description=None,
        )
        proto = ep._to_proto()
        restored = RegisteredServiceEndpoint._from_proto(proto)
        assert isinstance(restored, GeneralServiceEndpoint)
        assert restored.description is None

    def test_description_too_long_raises(self):
        # 101 UTF-8 bytes (e.g. 101 ASCII characters)
        long_desc = "x" * 101
        with pytest.raises(ValueError, match="100 UTF-8 bytes"):
            GeneralServiceEndpoint(
                ip_address=b"\x7f\x00\x00\x01",
                port=80,
                description=long_desc,
            )

    def test_multibyte_description_utf8_limit(self):
        # Each emoji is 4 UTF-8 bytes, 26 emojis = 104 bytes > 100
        long_desc = "\U0001f600" * 26
        with pytest.raises(ValueError, match="100 UTF-8 bytes"):
            GeneralServiceEndpoint(
                ip_address=b"\x7f\x00\x00\x01",
                port=80,
                description=long_desc,
            )


# --- Address validation tests ---


class TestAddressValidation:
    def test_ip_address_round_trip(self):
        ep = MirrorNodeServiceEndpoint(ip_address=b"\x7f\x00\x00\x01", port=443, requires_tls=True)
        proto = ep._to_proto()
        restored = RegisteredServiceEndpoint._from_proto(proto)
        assert restored.ip_address == b"\x7f\x00\x00\x01"
        assert restored.domain_name is None

    def test_domain_name_round_trip(self):
        ep = MirrorNodeServiceEndpoint(domain_name="mirror.hedera.com", port=443, requires_tls=True)
        proto = ep._to_proto()
        restored = RegisteredServiceEndpoint._from_proto(proto)
        assert restored.domain_name == "mirror.hedera.com"
        assert restored.ip_address is None

    def test_ipv6_round_trip(self):
        ipv6 = b"\x00" * 16
        ep = RpcRelayServiceEndpoint(ip_address=ipv6, port=8545, requires_tls=False)
        proto = ep._to_proto()
        restored = RegisteredServiceEndpoint._from_proto(proto)
        assert restored.ip_address == ipv6

    def test_both_ip_and_domain_raises(self):
        with pytest.raises(ValueError, match="Exactly one"):
            MirrorNodeServiceEndpoint(
                ip_address=b"\x7f\x00\x00\x01",
                domain_name="example.com",
                port=80,
            )

    def test_neither_ip_nor_domain_raises(self):
        with pytest.raises(ValueError, match="Exactly one"):
            MirrorNodeServiceEndpoint(port=80)

    def test_invalid_ip_length_raises(self):
        with pytest.raises(ValueError, match="4 bytes.*or 16 bytes"):
            MirrorNodeServiceEndpoint(ip_address=b"\x7f\x00\x00", port=80)

    def test_non_ascii_domain_raises(self):
        with pytest.raises(ValueError, match="ASCII"):
            MirrorNodeServiceEndpoint(domain_name="münchen.de", port=80)

    def test_domain_longer_than_250_raises(self):
        with pytest.raises(ValueError, match="250 characters"):
            MirrorNodeServiceEndpoint(domain_name="a" * 251, port=80)

    def test_port_below_zero_raises(self):
        with pytest.raises(ValueError, match="range 0 to 65535"):
            MirrorNodeServiceEndpoint(ip_address=b"\x7f\x00\x00\x01", port=-1)

    def test_port_above_65535_raises(self):
        with pytest.raises(ValueError, match="range 0 to 65535"):
            MirrorNodeServiceEndpoint(ip_address=b"\x7f\x00\x00\x01", port=65536)
