"""
TCK-aligned unit tests for registered node transactions.

These tests mirror the structure expected by the Hedera TCK (Technology
Compatibility Kit) for registered node operations. When TCK handlers are
added for registered nodes, these tests document the expected behaviour.

TODO: Add TCK JSON-RPC handlers (tck/handlers/registered_node.py) and
      corresponding param/response dataclasses once the TCK specification
      for registered nodes is finalized.
"""

from __future__ import annotations

import pytest

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
from hiero_sdk_python.address_book.general_service_endpoint import GeneralServiceEndpoint
from hiero_sdk_python.address_book.mirror_node_service_endpoint import MirrorNodeServiceEndpoint
from hiero_sdk_python.address_book.rpc_relay_service_endpoint import RpcRelayServiceEndpoint
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.nodes.registered_node_create_transaction import RegisteredNodeCreateTransaction
from hiero_sdk_python.nodes.registered_node_delete_transaction import RegisteredNodeDeleteTransaction
from hiero_sdk_python.nodes.registered_node_update_transaction import RegisteredNodeUpdateTransaction


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# RegisteredNodeCreateTransaction – TCK scenarios
# ---------------------------------------------------------------------------


class TestTckRegisteredNodeCreate:
    """TCK-style create scenarios."""

    def test_create_with_admin_key_and_block_endpoint(self):
        """TCK: createRegisteredNode with adminKey + BlockNodeServiceEndpoint."""
        admin_key = PrivateKey.generate_ed25519().public_key()
        ep = BlockNodeServiceEndpoint(
            domain_name="block.tck.example.com",
            port=443,
            requires_tls=True,
            endpoint_apis=[BlockNodeApi.STATUS, BlockNodeApi.SUBSCRIBE_STREAM],
        )
        tx = RegisteredNodeCreateTransaction()
        tx.set_admin_key(admin_key)
        tx.set_description("tck block node")
        tx.set_service_endpoints([ep])
        body = tx._build_proto_body()
        assert body.admin_key is not None
        assert body.description == "tck block node"
        assert len(body.service_endpoint) == 1

    def test_create_with_all_endpoint_types(self):
        """TCK: createRegisteredNode with every endpoint subtype."""
        admin_key = PrivateKey.generate_ed25519().public_key()
        endpoints = [
            BlockNodeServiceEndpoint(
                domain_name="block.tck.example.com",
                port=443,
                requires_tls=True,
                endpoint_apis=[BlockNodeApi.PUBLISH],
            ),
            MirrorNodeServiceEndpoint(
                domain_name="mirror.tck.example.com",
                port=5600,
                requires_tls=True,
            ),
            RpcRelayServiceEndpoint(
                domain_name="rpc.tck.example.com",
                port=7546,
                requires_tls=False,
            ),
            GeneralServiceEndpoint(
                domain_name="general.tck.example.com",
                port=8080,
                requires_tls=False,
                description="general svc",
            ),
        ]
        tx = RegisteredNodeCreateTransaction()
        tx.set_admin_key(admin_key)
        tx.set_service_endpoints(endpoints)
        body = tx._build_proto_body()
        assert len(body.service_endpoint) == 4

    def test_create_requires_admin_key(self):
        """TCK: createRegisteredNode without adminKey should raise."""
        ep = BlockNodeServiceEndpoint(
            domain_name="block.tck.example.com",
            port=443,
            requires_tls=True,
            endpoint_apis=[BlockNodeApi.STATUS],
        )
        tx = RegisteredNodeCreateTransaction()
        tx.set_service_endpoints([ep])
        with pytest.raises(ValueError, match="admin_key is required"):
            tx._build_proto_body()

    def test_create_requires_at_least_one_endpoint(self):
        """TCK: createRegisteredNode with empty endpoints should raise."""
        admin_key = PrivateKey.generate_ed25519().public_key()
        tx = RegisteredNodeCreateTransaction()
        tx.set_admin_key(admin_key)
        with pytest.raises(ValueError, match="at least 1"):
            tx._build_proto_body()

    def test_create_description_optional(self):
        """TCK: createRegisteredNode without description sets empty string."""
        admin_key = PrivateKey.generate_ed25519().public_key()
        ep = MirrorNodeServiceEndpoint(
            domain_name="mirror.tck.example.com",
            port=5600,
            requires_tls=True,
        )
        tx = RegisteredNodeCreateTransaction()
        tx.set_admin_key(admin_key)
        tx.set_service_endpoints([ep])
        body = tx._build_proto_body()
        assert body.description == ""


# ---------------------------------------------------------------------------
# RegisteredNodeUpdateTransaction – TCK scenarios
# ---------------------------------------------------------------------------


class TestTckRegisteredNodeUpdate:
    """TCK-style update scenarios."""

    def test_update_description(self):
        """TCK: updateRegisteredNode with new description."""
        tx = RegisteredNodeUpdateTransaction()
        tx.set_registered_node_id(42)
        tx.set_description("updated via tck")
        body = tx._build_proto_body()
        assert body.registered_node_id == 42
        assert body.description.value == "updated via tck"

    def test_update_service_endpoints(self):
        """TCK: updateRegisteredNode replacing service endpoints."""
        ep = RpcRelayServiceEndpoint(
            domain_name="rpc.tck.example.com",
            port=7546,
            requires_tls=False,
        )
        tx = RegisteredNodeUpdateTransaction()
        tx.set_registered_node_id(42)
        tx.set_service_endpoints([ep])
        body = tx._build_proto_body()
        assert len(body.service_endpoint) == 1

    def test_update_admin_key(self):
        """TCK: updateRegisteredNode rotating admin key."""
        new_key = PrivateKey.generate_ed25519().public_key()
        tx = RegisteredNodeUpdateTransaction()
        tx.set_registered_node_id(42)
        tx.set_admin_key(new_key)
        body = tx._build_proto_body()
        assert body.admin_key is not None

    def test_update_invalid_id_zero(self):
        """TCK: updateRegisteredNode with id=0 should raise on build."""
        tx = RegisteredNodeUpdateTransaction()
        tx.set_registered_node_id(0)
        with pytest.raises(ValueError):
            tx._build_proto_body()

    def test_update_invalid_id_negative(self):
        """TCK: updateRegisteredNode with negative id should raise on build."""
        tx = RegisteredNodeUpdateTransaction()
        tx.set_registered_node_id(-1)
        with pytest.raises(ValueError):
            tx._build_proto_body()


# ---------------------------------------------------------------------------
# RegisteredNodeDeleteTransaction – TCK scenarios
# ---------------------------------------------------------------------------


class TestTckRegisteredNodeDelete:
    """TCK-style delete scenarios."""

    def test_delete_by_id(self):
        """TCK: deleteRegisteredNode with valid id."""
        tx = RegisteredNodeDeleteTransaction()
        tx.set_registered_node_id(99)
        body = tx._build_proto_body()
        assert body.registered_node_id == 99

    def test_delete_invalid_id_zero(self):
        """TCK: deleteRegisteredNode with id=0 should raise on build."""
        tx = RegisteredNodeDeleteTransaction()
        tx.set_registered_node_id(0)
        with pytest.raises(ValueError):
            tx._build_proto_body()

    def test_delete_invalid_id_negative(self):
        """TCK: deleteRegisteredNode with negative id should raise on build."""
        tx = RegisteredNodeDeleteTransaction()
        tx.set_registered_node_id(-1)
        with pytest.raises(ValueError):
            tx._build_proto_body()
