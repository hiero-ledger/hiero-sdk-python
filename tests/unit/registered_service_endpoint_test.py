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
    """Tests for BlockNodeApi enum values."""

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
    """Tests for BlockNodeServiceEndpoint serialization and round-trip."""

    def test_round_trip_ip_address(self):
        """Verify round-trip with an IP address preserves all fields."""
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
        """Verify round-trip with a domain name preserves all fields."""
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
        """Verify multiple endpoint APIs survive round-trip serialization."""
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

    def test_empty_endpoint_apis_allowed(self):
        """Verify an empty endpoint_apis list is accepted."""
        ep = BlockNodeServiceEndpoint(
            ip_address=b"\x7f\x00\x00\x01",
            port=80,
            endpoint_apis=[],
        )
        assert ep.endpoint_apis == []

    def test_none_endpoint_apis_defaults_to_empty(self):
        """Verify None endpoint_apis defaults to an empty list."""
        ep = BlockNodeServiceEndpoint(
            ip_address=b"\x7f\x00\x00\x01",
            port=80,
            endpoint_apis=None,
        )
        assert ep.endpoint_apis == []


# --- MirrorNodeServiceEndpoint ---


class TestMirrorNodeServiceEndpoint:
    """Tests for MirrorNodeServiceEndpoint serialization and round-trip."""

    def test_round_trip(self):
        """Verify round-trip preserves all fields."""
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
    """Tests for RpcRelayServiceEndpoint serialization and round-trip."""

    def test_round_trip(self):
        """Verify round-trip preserves all fields."""
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
    """Tests for GeneralServiceEndpoint serialization and round-trip."""

    def test_round_trip_with_description(self):
        """Verify round-trip with a description preserves all fields."""
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
        """Verify round-trip without a description preserves None."""
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
        """Verify a description exceeding 100 UTF-8 bytes raises ValueError."""
        # 101 UTF-8 bytes (e.g. 101 ASCII characters)
        long_desc = "x" * 101
        with pytest.raises(ValueError, match="100 UTF-8 bytes"):
            GeneralServiceEndpoint(
                ip_address=b"\x7f\x00\x00\x01",
                port=80,
                description=long_desc,
            )

    def test_multibyte_description_utf8_limit(self):
        """Verify multi-byte characters are counted as UTF-8 bytes for the limit."""
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
    """Tests for ip_address vs domain_name address validation."""

    def test_ip_address_round_trip(self):
        """Verify IP address is preserved and domain_name is None after round-trip."""
        ep = MirrorNodeServiceEndpoint(ip_address=b"\x7f\x00\x00\x01", port=443, requires_tls=True)
        proto = ep._to_proto()
        restored = RegisteredServiceEndpoint._from_proto(proto)
        assert restored.ip_address == b"\x7f\x00\x00\x01"
        assert restored.domain_name is None

    def test_domain_name_round_trip(self):
        """Verify domain name is preserved and ip_address is None after round-trip."""
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

    def test_neither_ip_nor_domain_allowed_for_builder_pattern(self):
        """Constructor allows neither address for builder/setter pattern; _to_proto raises."""
        ep = MirrorNodeServiceEndpoint(port=80)
        assert ep.ip_address is None
        assert ep.domain_name is None
        with pytest.raises(ValueError, match="serialization"):
            ep._to_proto()

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


# --- Setter tests ---


class TestRegisteredServiceEndpointSetters:
    """Tests for set_* methods on RegisteredServiceEndpoint and subclasses."""

    def test_set_ip_address_clears_domain(self):
        """Verify set_ip_address replaces domain_name with ip_address."""
        ep = MirrorNodeServiceEndpoint(domain_name="example.com", port=443)
        result = ep.set_ip_address(b"\x7f\x00\x00\x01")
        assert result is ep
        assert ep.ip_address == b"\x7f\x00\x00\x01"
        assert ep.domain_name is None

    def test_set_domain_name_clears_ip(self):
        """Verify set_domain_name replaces ip_address with domain_name."""
        ep = MirrorNodeServiceEndpoint(ip_address=b"\x7f\x00\x00\x01", port=443)
        result = ep.set_domain_name("example.com")
        assert result is ep
        assert ep.domain_name == "example.com"
        assert ep.ip_address is None

    def test_set_port(self):
        """Verify set_port updates the port."""
        ep = MirrorNodeServiceEndpoint(domain_name="example.com", port=80)
        result = ep.set_port(443)
        assert result is ep
        assert ep.port == 443

    def test_set_port_rejects_invalid(self):
        """Verify set_port rejects an out-of-range port."""
        ep = MirrorNodeServiceEndpoint(domain_name="example.com", port=80)
        with pytest.raises(ValueError, match="range 0 to 65535"):
            ep.set_port(70000)

    def test_set_requires_tls(self):
        """Verify set_requires_tls updates the flag."""
        ep = MirrorNodeServiceEndpoint(domain_name="example.com", port=443, requires_tls=False)
        result = ep.set_requires_tls(True)
        assert result is ep
        assert ep.requires_tls is True

    def test_set_requires_tls_rejects_non_bool(self):
        """Verify set_requires_tls rejects non-bool values."""
        ep = MirrorNodeServiceEndpoint(domain_name="example.com", port=443)
        with pytest.raises(ValueError, match="requires_tls must be a bool"):
            ep.set_requires_tls("yes")

    def test_set_ip_address_rejects_invalid(self):
        """Verify set_ip_address rejects invalid byte lengths."""
        ep = MirrorNodeServiceEndpoint(domain_name="example.com", port=80)
        with pytest.raises(ValueError, match="ip_address"):
            ep.set_ip_address(b"\x7f\x00")

    def test_set_domain_name_rejects_non_ascii(self):
        """Verify set_domain_name rejects non-ASCII strings."""
        ep = MirrorNodeServiceEndpoint(ip_address=b"\x7f\x00\x00\x01", port=80)
        with pytest.raises(ValueError, match="ASCII"):
            ep.set_domain_name("münchen.de")

    def test_set_endpoint_apis_on_block_node(self):
        """Verify set_endpoint_apis replaces the API list on BlockNodeServiceEndpoint."""
        ep = BlockNodeServiceEndpoint(
            domain_name="block.example.com",
            port=443,
            endpoint_apis=[BlockNodeApi.OTHER],
        )
        result = ep.set_endpoint_apis([BlockNodeApi.PUBLISH, BlockNodeApi.STATUS])
        assert result is ep
        assert ep.endpoint_apis == [BlockNodeApi.PUBLISH, BlockNodeApi.STATUS]

    def test_set_description_on_general_endpoint(self):
        """Verify set_description updates the description on GeneralServiceEndpoint."""
        ep = GeneralServiceEndpoint(
            domain_name="general.example.com",
            port=80,
            description="old",
        )
        result = ep.set_description("new description")
        assert result is ep
        assert ep.description == "new description"

    def test_set_description_none(self):
        """Verify set_description accepts None."""
        ep = GeneralServiceEndpoint(
            domain_name="general.example.com",
            port=80,
            description="something",
        )
        ep.set_description(None)
        assert ep.description is None

    def test_set_description_rejects_too_long(self):
        """Verify set_description rejects descriptions over 100 UTF-8 bytes."""
        ep = GeneralServiceEndpoint(domain_name="general.example.com", port=80)
        with pytest.raises(ValueError, match="100 UTF-8 bytes"):
            ep.set_description("x" * 101)


# --- _from_dict tests ---


class TestFromDict:
    """Tests for _from_dict deserialization from mirror-node JSON."""

    def test_from_dict_ip_address_parsing(self):
        """Verify _from_dict correctly parses IP address strings."""
        data = {
            "ip_address": "192.168.1.1",
            "port": 443,
            "requires_tls": True,
            "type": "MIRROR_NODE",
        }
        ep = RegisteredServiceEndpoint._from_dict(data)
        assert isinstance(ep, MirrorNodeServiceEndpoint)
        assert ep.ip_address == b"\xc0\xa8\x01\x01"
        assert ep.domain_name is None

    def test_from_dict_unknown_type_raises(self):
        """Verify _from_dict raises ValueError for unknown endpoint types."""
        data = {
            "domain_name": "example.com",
            "port": 80,
            "type": "UNKNOWN_TYPE",
        }
        with pytest.raises(ValueError, match="Unknown endpoint type"):
            RegisteredServiceEndpoint._from_dict(data)

    def test_from_dict_rpc_relay(self):
        """Verify _from_dict correctly parses an RPC_RELAY endpoint."""
        data = {
            "domain_name": "relay.example.com",
            "port": 7546,
            "requires_tls": True,
            "type": "RPC_RELAY",
        }
        ep = RegisteredServiceEndpoint._from_dict(data)
        assert isinstance(ep, RpcRelayServiceEndpoint)
        assert ep.domain_name == "relay.example.com"

    def test_from_dict_general_service(self):
        """Verify _from_dict correctly parses a GENERAL_SERVICE endpoint."""
        data = {
            "domain_name": "gen.example.com",
            "port": 9000,
            "type": "GENERAL_SERVICE",
            "general_service": {"description": "my service"},
        }
        ep = RegisteredServiceEndpoint._from_dict(data)
        assert isinstance(ep, GeneralServiceEndpoint)
        assert ep.description == "my service"
