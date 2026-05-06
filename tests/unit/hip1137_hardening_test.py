"""Phase 6 hardening tests — validation, status codes, retry, exports."""

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
# HIP-1137 status codes in ResponseCode enum
# ---------------------------------------------------------------------------


class TestHip1137StatusCodes:
    """Verify all HIP-1137 status codes are present in the SDK ResponseCode enum."""

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
        """HIP-1137 statuses must NOT be in the retryable set."""
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
    def test_ip_address_not_bytes(self):
        with pytest.raises(ValueError, match="ip_address"):
            RegisteredServiceEndpoint(ip_address="192.168.1.1", port=80)

    def test_domain_name_not_str(self):
        with pytest.raises((ValueError, TypeError)):
            RegisteredServiceEndpoint(domain_name=12345, port=80)

    def test_port_not_int(self):
        with pytest.raises(ValueError, match="port"):
            RegisteredServiceEndpoint(domain_name="example.com", port="80")

    def test_port_is_bool(self):
        with pytest.raises(ValueError, match="port"):
            RegisteredServiceEndpoint(domain_name="example.com", port=True)

    def test_requires_tls_not_bool(self):
        with pytest.raises(ValueError, match="requires_tls"):
            RegisteredServiceEndpoint(domain_name="example.com", port=80, requires_tls="yes")

    def test_block_node_invalid_endpoint_api_item(self):
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
        # Each emoji is 4 UTF-8 bytes. 26 emojis = 104 bytes > 100 limit.
        long_desc = "\U0001f600" * 26
        assert len(long_desc.encode("utf-8")) > 100
        with pytest.raises(ValueError, match="100 UTF-8 bytes"):
            GeneralServiceEndpoint(domain_name="g.example.com", port=80, description=long_desc)

    def test_general_endpoint_description_exactly_100_bytes(self):
        # 25 emojis = exactly 100 UTF-8 bytes — should succeed
        desc = "\U0001f600" * 25
        assert len(desc.encode("utf-8")) == 100
        ep = GeneralServiceEndpoint(domain_name="g.example.com", port=80, description=desc)
        assert ep.description == desc


# ---------------------------------------------------------------------------
# RegisteredNodeCreateTransaction validation
# ---------------------------------------------------------------------------


class TestRegisteredNodeCreateTransactionValidation:
    def test_missing_admin_key_fails(self):
        tx = RegisteredNodeCreateTransaction()
        tx.set_service_endpoints([_mirror_ep()])
        with pytest.raises(ValueError, match="admin_key is required"):
            tx._build_proto_body()

    def test_invalid_endpoint_object_fails(self):
        tx = RegisteredNodeCreateTransaction()
        tx.admin_key = _make_key()
        tx.service_endpoints = ["not an endpoint"]
        with pytest.raises(TypeError, match="RegisteredServiceEndpoint"):
            tx._build_proto_body()

    def test_valid_build_succeeds(self):
        tx = RegisteredNodeCreateTransaction()
        tx.admin_key = _make_key()
        tx.set_service_endpoints([_mirror_ep()])
        body = tx._build_proto_body()
        assert body.HasField("admin_key")


# ---------------------------------------------------------------------------
# RegisteredNodeUpdateTransaction validation
# ---------------------------------------------------------------------------


class TestRegisteredNodeUpdateTransactionValidation:
    def test_registered_node_id_zero_fails(self):
        tx = RegisteredNodeUpdateTransaction()
        tx.registered_node_id = 0
        with pytest.raises(ValueError, match="positive integer"):
            tx._build_proto_body()

    def test_registered_node_id_negative_fails(self):
        tx = RegisteredNodeUpdateTransaction()
        tx.registered_node_id = -5
        with pytest.raises(ValueError, match="positive integer"):
            tx._build_proto_body()

    def test_empty_service_endpoints_fails(self):
        tx = RegisteredNodeUpdateTransaction()
        tx.registered_node_id = 1
        tx.service_endpoints = []
        with pytest.raises(ValueError, match="at least 1 entry"):
            tx._build_proto_body()

    def test_invalid_endpoint_object_fails(self):
        tx = RegisteredNodeUpdateTransaction()
        tx.registered_node_id = 1
        tx.service_endpoints = [42]
        with pytest.raises(TypeError, match="RegisteredServiceEndpoint"):
            tx._build_proto_body()


# ---------------------------------------------------------------------------
# RegisteredNodeDeleteTransaction validation
# ---------------------------------------------------------------------------


class TestRegisteredNodeDeleteTransactionValidation:
    def test_registered_node_id_zero_fails(self):
        tx = RegisteredNodeDeleteTransaction()
        tx.registered_node_id = 0
        with pytest.raises(ValueError, match="positive integer"):
            tx._build_proto_body()

    def test_registered_node_id_negative_fails(self):
        tx = RegisteredNodeDeleteTransaction()
        tx.registered_node_id = -1
        with pytest.raises(ValueError, match="positive integer"):
            tx._build_proto_body()

    def test_registered_node_id_bool_fails(self):
        tx = RegisteredNodeDeleteTransaction()
        tx.registered_node_id = True
        with pytest.raises(ValueError, match="positive integer"):
            tx._build_proto_body()


# ---------------------------------------------------------------------------
# associated_registered_nodes rejects non-int
# ---------------------------------------------------------------------------


class TestAssociatedRegisteredNodesNonInt:
    def test_node_create_rejects_string_id(self):
        from hiero_sdk_python.nodes.node_create_transaction import NodeCreateTransaction

        tx = NodeCreateTransaction()
        tx.set_associated_registered_nodes(["abc"])
        with pytest.raises(ValueError, match="positive integer"):
            tx._validate_associated_registered_nodes(tx.associated_registered_nodes)

    def test_node_update_rejects_float_id(self):
        from hiero_sdk_python.nodes.node_update_transaction import NodeUpdateTransaction

        tx = NodeUpdateTransaction()
        tx.set_associated_registered_nodes([1.5])
        with pytest.raises(ValueError, match="positive integer"):
            tx._validate_associated_registered_nodes(tx.associated_registered_nodes)


# ---------------------------------------------------------------------------
# Public imports
# ---------------------------------------------------------------------------


class TestPublicImports:
    """All intended HIP-1137 public classes must be importable from the package."""

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
