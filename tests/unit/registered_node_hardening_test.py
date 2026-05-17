"""Hardening tests for registered node validation, status codes, retry, and exports."""

from __future__ import annotations

import pytest

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
from hiero_sdk_python.address_book.general_service_endpoint import GeneralServiceEndpoint
from hiero_sdk_python.address_book.mirror_node_service_endpoint import MirrorNodeServiceEndpoint
from hiero_sdk_python.address_book.registered_service_endpoint import RegisteredServiceEndpoint
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.nodes.registered_node_create_transaction import RegisteredNodeCreateTransaction
from hiero_sdk_python.nodes.registered_node_delete_transaction import RegisteredNodeDeleteTransaction
from hiero_sdk_python.nodes.registered_node_update_transaction import RegisteredNodeUpdateTransaction
from hiero_sdk_python.response_code import ResponseCode


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _mirror_ep() -> MirrorNodeServiceEndpoint:
    return MirrorNodeServiceEndpoint(domain_name="m.example.com", port=443, requires_tls=True)


def _make_key():
    return PrivateKey.generate().public_key()


# ---------------------------------------------------------------------------
# Registered node status codes in ResponseCode enum
# ---------------------------------------------------------------------------


class TestRegisteredNodeStatusCodes:
    """Verify all registered node status codes are present in the SDK ResponseCode enum."""

    @pytest.mark.parametrize(
        "name,value",
        [
            ("INVALID_REGISTERED_NODE_ID", 529),
            ("INVALID_REGISTERED_ENDPOINT", 530),
            ("REGISTERED_ENDPOINTS_EXCEEDED_LIMIT", 531),
            ("INVALID_REGISTERED_ENDPOINT_ADDRESS", 532),
            ("INVALID_REGISTERED_ENDPOINT_TYPE", 533),
            ("REGISTERED_NODE_STILL_ASSOCIATED", 534),
            ("MAX_REGISTERED_NODES_EXCEEDED", 535),
        ],
    )
    def test_status_code_exists(self, name, value):
        code = ResponseCode(value)
        assert code.name == name
        assert code.value == value
        assert not code.is_unknown

    @pytest.mark.parametrize(
        "value",
        [529, 530, 531, 532, 533, 534, 535],
    )
    def test_status_codes_are_not_retryable(self, value):
        """Registered node statuses must NOT be in the retryable set."""
        # The SDK retry classifier only retries these 4 statuses
        retryable = {
            ResponseCode.PLATFORM_TRANSACTION_NOT_CREATED,
            ResponseCode.PLATFORM_NOT_ACTIVE,
            ResponseCode.BUSY,
            ResponseCode.INVALID_NODE_ACCOUNT,
        }
        code = ResponseCode(value)
        assert code not in retryable

    def test_status_codes_match_protobuf(self):
        """SDK enum values must match generated protobuf values."""
        from hiero_sdk_python.hapi.services.response_code_pb2 import ResponseCodeEnum

        for name in [
            "INVALID_REGISTERED_NODE_ID",
            "INVALID_REGISTERED_ENDPOINT",
            "REGISTERED_ENDPOINTS_EXCEEDED_LIMIT",
            "INVALID_REGISTERED_ENDPOINT_ADDRESS",
            "INVALID_REGISTERED_ENDPOINT_TYPE",
            "REGISTERED_NODE_STILL_ASSOCIATED",
            "MAX_REGISTERED_NODES_EXCEEDED",
        ]:
            proto_val = ResponseCodeEnum.Value(name)
            sdk_code = ResponseCode[name]
            assert sdk_code.value == proto_val, f"{name}: SDK={sdk_code.value} != proto={proto_val}"


# ---------------------------------------------------------------------------
# Endpoint validation edge cases
# ---------------------------------------------------------------------------


class TestEndpointValidationEdgeCases:
    """Tests for edge-case validation of RegisteredServiceEndpoint fields."""

    def test_ip_address_not_bytes(self):
        """Verify passing a string as ip_address raises ValueError."""
        with pytest.raises(ValueError, match="ip_address"):
            RegisteredServiceEndpoint(ip_address="192.168.1.1", port=80)

    def test_domain_name_not_str(self):
        """Verify passing a non-string as domain_name raises an error."""
        with pytest.raises((ValueError, TypeError)):
            RegisteredServiceEndpoint(domain_name=12345, port=80)

    def test_port_not_int(self):
        """Verify passing a string as port raises ValueError."""
        with pytest.raises(ValueError, match="port"):
            RegisteredServiceEndpoint(domain_name="example.com", port="80")

    def test_port_is_bool(self):
        """Verify passing a bool as port raises ValueError."""
        with pytest.raises(ValueError, match="port"):
            RegisteredServiceEndpoint(domain_name="example.com", port=True)

    def test_requires_tls_not_bool(self):
        """Verify passing a non-bool as requires_tls raises ValueError."""
        with pytest.raises(ValueError, match="requires_tls"):
            RegisteredServiceEndpoint(domain_name="example.com", port=80, requires_tls="yes")

    def test_block_node_invalid_endpoint_api_item(self):
        """Verify an invalid BlockNodeApi value raises an error."""
        with pytest.raises((ValueError, KeyError)):
            BlockNodeServiceEndpoint(
                domain_name="block.example.com",
                port=443,
                endpoint_apis=[999],  # not a valid BlockNodeApi
            )

    def test_block_node_endpoint_apis_accepts_int_enum_values(self):
        """BlockNodeApi(0) is OTHER — ints that map to valid enum values are accepted."""
        ep = BlockNodeServiceEndpoint(
            domain_name="block.example.com",
            port=443,
            endpoint_apis=[0, 1],  # OTHER=0, STATUS=1
        )
        assert ep.endpoint_apis == [BlockNodeApi.OTHER, BlockNodeApi.STATUS]

    def test_general_endpoint_description_multibyte_utf8(self):
        """Verify a description exceeding 100 UTF-8 bytes raises ValueError."""
        # Each emoji is 4 UTF-8 bytes. 26 emojis = 104 bytes > 100 limit.
        long_desc = "\U0001f600" * 26
        assert len(long_desc.encode("utf-8")) > 100
        with pytest.raises(ValueError, match="100 UTF-8 bytes"):
            GeneralServiceEndpoint(domain_name="g.example.com", port=80, description=long_desc)

    def test_general_endpoint_description_exactly_100_bytes(self):
        """Verify a description of exactly 100 UTF-8 bytes is accepted."""
        # 25 emojis = exactly 100 UTF-8 bytes — should succeed
        desc = "\U0001f600" * 25
        assert len(desc.encode("utf-8")) == 100
        ep = GeneralServiceEndpoint(domain_name="g.example.com", port=80, description=desc)
        assert ep.description == desc


# ---------------------------------------------------------------------------
# RegisteredNodeCreateTransaction validation
# ---------------------------------------------------------------------------


class TestRegisteredNodeCreateTransactionValidation:
    """Tests for RegisteredNodeCreateTransaction build validation."""

    def test_valid_build_succeeds(self):
        """Verify a valid transaction with admin_key and endpoints builds successfully."""
        tx = RegisteredNodeCreateTransaction()
        tx.admin_key = _make_key()
        tx.set_service_endpoints([_mirror_ep()])
        body = tx._build_proto_body()
        assert body.HasField("admin_key")

        # endpoint wrapper assertions
        endpoint = body.service_endpoint[0]

        assert endpoint.HasField("mirror_node")
        assert not endpoint.HasField("block_node")
        assert not endpoint.HasField("rpc_relay")
        assert not endpoint.HasField("general_service")

        # endpoint field assertions
        assert endpoint.domain_name == "m.example.com"
        assert endpoint.port == 443
        assert endpoint.requires_tls is True

    def test_build_without_admin_key_succeeds(self):
        """admin_key is no longer validated client-side; the node handles it."""
        tx = RegisteredNodeCreateTransaction()
        tx.set_service_endpoints([_mirror_ep()])
        body = tx._build_proto_body()
        assert not body.HasField("admin_key")

    def test_build_without_endpoints_succeeds(self):
        """service_endpoints are no longer validated client-side; the node handles it."""
        tx = RegisteredNodeCreateTransaction()
        tx.admin_key = _make_key()
        body = tx._build_proto_body()
        assert len(body.service_endpoint) == 0


# ---------------------------------------------------------------------------
# RegisteredNodeUpdateTransaction validation
# ---------------------------------------------------------------------------


class TestRegisteredNodeUpdateTransactionValidation:
    """Tests for RegisteredNodeUpdateTransaction build validation."""

    def test_build_with_valid_id_succeeds(self):
        """Verify building with a valid registered_node_id succeeds."""
        tx = RegisteredNodeUpdateTransaction()
        tx.registered_node_id = 1
        body = tx._build_proto_body()
        assert body.registered_node_id == 1

    def test_build_with_endpoints_succeeds(self):
        """Verify building with service endpoints succeeds."""
        tx = RegisteredNodeUpdateTransaction()
        tx.registered_node_id = 1
        tx.service_endpoints = [_mirror_ep()]
        body = tx._build_proto_body()
        assert len(body.service_endpoint) == 1


# ---------------------------------------------------------------------------
# RegisteredNodeDeleteTransaction validation
# ---------------------------------------------------------------------------


class TestRegisteredNodeDeleteTransactionValidation:
    """Tests for RegisteredNodeDeleteTransaction build validation."""

    def test_registered_node_id_zero_fails(self):
        """Verify registered_node_id of zero raises ValueError."""
        tx = RegisteredNodeDeleteTransaction()
        tx.registered_node_id = 0
        with pytest.raises(ValueError, match="positive integer"):
            tx._build_proto_body()

    def test_registered_node_id_negative_fails(self):
        """Verify negative registered_node_id raises ValueError."""
        tx = RegisteredNodeDeleteTransaction()
        tx.registered_node_id = -1
        with pytest.raises(ValueError, match="positive integer"):
            tx._build_proto_body()

    def test_registered_node_id_bool_fails(self):
        """Verify bool registered_node_id raises ValueError."""
        tx = RegisteredNodeDeleteTransaction()
        tx.registered_node_id = True
        with pytest.raises(ValueError, match="positive integer"):
            tx._build_proto_body()


# ---------------------------------------------------------------------------
# associated_registered_nodes rejects non-int
# ---------------------------------------------------------------------------


class TestAssociatedRegisteredNodesNonInt:
    """Tests for associated_registered_nodes accepting non-int values."""

    def test_node_create_accepts_any_values(self):
        """Validation is now delegated to the consensus node."""
        from hiero_sdk_python.nodes.node_create_transaction import NodeCreateTransaction

        tx = NodeCreateTransaction()
        tx.set_associated_registered_nodes(["abc"])
        assert tx.associated_registered_nodes == ["abc"]

    def test_node_update_accepts_any_values(self):
        """Validation is now delegated to the consensus node."""
        from hiero_sdk_python.nodes.node_update_transaction import NodeUpdateTransaction

        tx = NodeUpdateTransaction()
        tx.set_associated_registered_nodes([1.5])
        assert tx.associated_registered_nodes == [1.5]


# ---------------------------------------------------------------------------
# Public imports
# ---------------------------------------------------------------------------


class TestPublicImports:
    """All registered node public classes must be importable from the package."""

    @pytest.mark.parametrize(
        "name",
        [
            "BlockNodeApi",
            "RegisteredServiceEndpoint",
            "BlockNodeServiceEndpoint",
            "MirrorNodeServiceEndpoint",
            "RpcRelayServiceEndpoint",
            "GeneralServiceEndpoint",
            "RegisteredNodeCreateTransaction",
            "RegisteredNodeUpdateTransaction",
            "RegisteredNodeDeleteTransaction",
            "RegisteredNode",
            "RegisteredNodeAddressBook",
            "RegisteredNodeAddressBookQuery",
        ],
    )
    def test_importable(self, name):
        import hiero_sdk_python

        cls = getattr(hiero_sdk_python, name)
        assert cls is not None

    @pytest.mark.parametrize(
        "name",
        [
            "BlockNodeApi",
            "BlockNodeServiceEndpoint",
            "GeneralServiceEndpoint",
            "MirrorNodeServiceEndpoint",
            "RegisteredServiceEndpoint",
            "RpcRelayServiceEndpoint",
            "RegisteredNodeCreateTransaction",
            "RegisteredNodeUpdateTransaction",
            "RegisteredNodeDeleteTransaction",
            "RegisteredNode",
            "RegisteredNodeAddressBook",
            "RegisteredNodeAddressBookQuery",
        ],
    )
    def test_in_all(self, name):
        import hiero_sdk_python

        assert name in hiero_sdk_python.__all__
